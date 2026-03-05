import requests
import os

OPEN_METEO_GEOCODE_API = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_FORECAST_API = "https://api.open-meteo.com/v1/forecast"


def _weather_code_to_description(code: int) -> str:
    if code == 0:
        return "Clear"
    if code == 1:
        return "Mainly clear"
    if code == 2:
        return "Partly cloudy"
    if code == 3:
        return "Overcast"
    if code in (45, 48):
        return "Fog"
    if code in (51, 53, 55, 56, 57):
        return "Drizzle"
    if code in (61, 63, 65, 66, 67):
        return "Rain"
    if code in (71, 73, 75, 77):
        return "Snow"
    if code in (80, 81, 82):
        return "Rain showers"
    if code in (85, 86):
        return "Snow showers"
    if code in (95, 96, 99):
        return "Thunderstorm"
    return f"Weather({code})"


# Common country names -> ISO 3166-1 alpha-2 (for API countryCode when user passes full name)
_COUNTRY_TO_CODE = {
    "india": "IN", "united states": "US", "usa": "US", "united kingdom": "GB", "uk": "GB",
    "germany": "DE", "france": "FR", "japan": "JP", "china": "CN", "australia": "AU",
    "brazil": "BR", "canada": "CA", "italy": "IT", "spain": "ES", "mexico": "MX",
    "russia": "RU", "south korea": "KR", "indonesia": "ID", "philippines": "PH",
    "netherlands": "NL", "turkey": "TR", "switzerland": "CH", "poland": "PL",
    "thailand": "TH", "vietnam": "VN", "egypt": "EG", "south africa": "ZA",
    "nigeria": "NG", "kenya": "KE", "argentina": "AR", "colombia": "CO", "pakistan": "PK",
    "bangladesh": "BD", "malaysia": "MY", "singapore": "SG", "uae": "AE",
    "united arab emirates": "AE", "saudi arabia": "SA", "israel": "IL", "portugal": "PT",
    "greece": "GR", "belgium": "BE", "austria": "AT", "sweden": "SE", "norway": "NO",
    "denmark": "DK", "finland": "FI", "ireland": "IE", "new zealand": "NZ",
}


def get_weather(city: str, country: str | None = None, *, timeout_s: int = 15) -> str:
    """
    Fetch real-time weather for a city using free Open-Meteo APIs (no API key).
    - city: city or place name (e.g. "Goa", "Paris").
    - country: optional; full name ("India") or ISO code ("IN") for precise matching.
    - Geocoding: resolves city (+ country) -> latitude/longitude
    - Forecast: returns current temperature + weather code
    """
    city = (city or "").strip()
    if not city:
        return "City name is required"

    def _norm(s: str) -> str:
        return " ".join((s or "").strip().lower().split())

    # Resolve country to API countryCode (ISO 3166-1 alpha-2) if provided
    country_code = None
    country_hint = (country or "").strip()
    if country_hint:
        if len(country_hint) == 2:
            country_code = country_hint.upper()
        else:
            country_code = _COUNTRY_TO_CODE.get(_norm(country_hint))

    try:
        # Allow inputs like "Goa, India" while still querying geocoder effectively.
        raw_parts = [p.strip() for p in city.split(",") if p.strip()]
        name_query = raw_parts[0]
        hint_parts = [p.lower() for p in raw_parts[1:]]

        geo_params = {
            "name": name_query,
            "count": 15,
            "language": "en",
            "format": "json",
        }
        if country_code:
            geo_params["countryCode"] = country_code

        geo_resp = requests.get(
            OPEN_METEO_GEOCODE_API,
            params=geo_params,
            timeout=timeout_s,
        )
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()
        results = geo_data.get("results") or []
        if not results:
            return f"City not found: {city}" + (f" in {country_hint}" if country_hint else "")

        # If country was given as full name (no code sent to API), filter by country name
        if country_hint and not country_code:
            country_norm = _norm(country_hint)
            results = [
                r for r in results
                if country_norm in _norm(r.get("country") or "") or _norm(r.get("country_code") or "") == country_norm
            ]
            if not results:
                return f"City not found: {city} in {country_hint}"

        # Prefer exact city-name matches (e.g., "Goa" over "Genoa").
        exact = [r for r in results if _norm(r.get("name")) == _norm(name_query)]

        def _hint_score(r: dict) -> int:
            hay = " ".join(
                [
                    _norm(r.get("admin1")),
                    _norm(r.get("admin2")),
                    _norm(r.get("admin3")),
                    _norm(r.get("admin4")),
                    _norm(r.get("country")),
                    _norm(r.get("country_code")),
                ]
            )
            return sum(1 for h in hint_parts if h and h in hay)

        candidates = exact or results
        candidates = sorted(
            candidates,
            key=lambda r: (
                _hint_score(r),
                float(r.get("population") or 0),
            ),
            reverse=True,
        )
        place = candidates[0]
        lat = place["latitude"]
        lon = place["longitude"]
        place_name = place.get("name") or city
        admin1 = place.get("admin1")
        country_label = place.get("country")
        label_parts = [place_name]
        if admin1:
            label_parts.append(admin1)
        if country_label:
            label_parts.append(country_label)
        resolved_label = ", ".join(label_parts)

        wx_resp = requests.get(
            OPEN_METEO_FORECAST_API,
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weather_code",
                "temperature_unit": "celsius",
                "timezone": "auto",
            },
            timeout=timeout_s,
        )
        wx_resp.raise_for_status()
        wx_data = wx_resp.json()
        current = wx_data.get("current") or {}

        temp_c = current["temperature_2m"]
        code = int(current["weather_code"])
        desc = _weather_code_to_description(code)
        return f"{resolved_label}: {desc} {temp_c}°C"
    except requests.RequestException:
        return "Not able to fetch the weather of requested city"
    except (KeyError, TypeError, ValueError):
        return "Weather API returned an unexpected response"


def run_cmd(cmd: str):
    return os.system(cmd)