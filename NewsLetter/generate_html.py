import re


# ---------------------------------------------------------------------------
# Markdown → HTML parser (email-safe)
# ---------------------------------------------------------------------------

def parse_markdown_to_html(text, accent_color="#667eea"):
    """Convert markdown-style AI output to clean, email-safe HTML.

    Handles:
    - # H1  → <h3> (banner / summary box)
    - ## H2 → <h2> (news item headline)
    - **bold** labels on their own line → <p class="label">
    - **bold** inline → <strong>
    - ``` code fences ``` → removed (AI examples are usually hypothetical)
    - ✔ / • / - / * bullet lines → <ul><li> lists
    - Source: ... lines → styled <p class="source">
    - Blank-line-separated text blocks → <p> paragraphs
    - ---- separators → removed
    """

    # 1. Remove raw code fences entirely (``` ... ```)
    text = re.sub(r'```[\s\S]*?```', '', text)

    # 2. Split into lines for processing
    lines = text.split('\n')
    output_lines = []
    in_ul = False

    def close_ul():
        nonlocal in_ul
        if in_ul:
            output_lines.append('</ul>')
            in_ul = False

    def open_ul():
        nonlocal in_ul
        if not in_ul:
            output_lines.append('<ul>')
            in_ul = True

    for line in lines:
        stripped = line.strip()

        # Skip horizontal separators
        if re.match(r'^-{3,}$', stripped):
            close_ul()
            continue

        # H1 → green summary banner
        m = re.match(r'^# (.+)$', stripped)
        if m:
            close_ul()
            output_lines.append(f'<h3>{m.group(1)}</h3>')
            continue

        # H2 / H3 → news item headline (h2 styled as card title)
        m = re.match(r'^#{2,3} (.+)$', stripped)
        if m:
            close_ul()
            output_lines.append(f'<h2>{m.group(1)}</h2>')
            continue

        # Bullet lines: ✔ • - * (but not separators like ---)
        if re.match(r'^[✔•\-\*]\s+.+', stripped):
            # Convert inline **bold** inside bullet
            bullet_text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', stripped)
            # Strip leading bullet character
            bullet_text = re.sub(r'^[✔•\-\*]\s+', '', bullet_text)
            open_ul()
            output_lines.append(f'  <li>{bullet_text}</li>')
            continue

        # Source: lines
        if re.match(r'^[•\-]?\s*Source.*:', stripped, re.IGNORECASE) or \
           re.match(r'^•\s+\w', stripped):
            close_ul()
            src = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', stripped)
            output_lines.append(f'<p class="source">{src}</p>')
            continue

        # **Bold label** on its own line → styled label
        if re.match(r'^\*\*[^*]+\*\*\s*$', stripped):
            close_ul()
            label = re.sub(r'^\*\*(.+?)\*\*\s*$', r'\1', stripped)
            output_lines.append(f'<p class="label">{label}</p>')
            continue

        # Empty line → close list, add paragraph break marker
        if not stripped:
            close_ul()
            output_lines.append('')
            continue

        # Regular text line — convert inline **bold** and output as-is
        close_ul()
        inline = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', stripped)
        output_lines.append(inline)

    close_ul()

    # 3. Merge consecutive non-empty lines into <p> blocks
    html_parts = []
    paragraph_lines = []

    def flush_paragraph():
        if paragraph_lines:
            combined = ' '.join(paragraph_lines)
            html_parts.append(f'<p>{combined}</p>')
            paragraph_lines.clear()

    for line in output_lines:
        if line.startswith('<h') or line.startswith('<ul') or \
           line.startswith('</ul') or line.startswith('  <li') or \
           line.startswith('<p class=') or line == '':
            flush_paragraph()
            if line:
                html_parts.append(line)
        else:
            paragraph_lines.append(line)

    flush_paragraph()

    # 4. Add card-p class to plain <p> tags so dark mode can target them
    result = '\n'.join(html_parts)
    result = re.sub(r'^<p>(.+)', r'<p class="card-p">\1', result, flags=re.MULTILINE)
    return result


# ---------------------------------------------------------------------------
# Shared HTML template builder
# ---------------------------------------------------------------------------

def _build_html_template(formatted_content, title, subtitle, accent, header_bg):
    return f"""<!DOCTYPE html>
<html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="color-scheme" content="light dark">
    <meta name="supported-color-schemes" content="light dark">
    <title>{title}</title>
    <style>
        :root {{
            color-scheme: light dark;
            supported-color-schemes: light dark;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-text-size-adjust: none;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: {header_bg.split(',')[0].strip("linear-gradient(135deg, ")[:7] if 'linear' in header_bg else header_bg};
            background-image: {header_bg};
            margin: 0;
            padding: 40px 20px;
            color: #1a1a1a;
            line-height: 1.75;
        }}

        .container {{
            max-width: 620px;
            margin: 0 auto;
            background-color: #ffffff;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.25);
        }}

        /* ── Header ── */
        .email-header {{
            background: {header_bg};
            padding: 36px 40px 28px;
            text-align: center;
        }}
        .email-header h1 {{
            color: #ffffff;
            font-size: 26px;
            font-weight: 800;
            letter-spacing: -0.3px;
            margin-bottom: 6px;
        }}
        .subtitle {{
            color: rgba(255,255,255,0.82);
            font-size: 13px;
            letter-spacing: 0.3px;
        }}

        /* ── Content area ── */
        .content {{
            padding: 32px 40px;
            font-size: 15px;
            color: #2d3748;
        }}

        /* AI SUMMARY / RADAR banner */
        h3 {{
            font-size: 13px;
            font-weight: 700;
            color: #fff;
            background: {accent};
            padding: 10px 18px;
            border-radius: 6px;
            text-align: center;
            margin-bottom: 16px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        /* Summary intro paragraph right after h3 */
        h3 + p {{
            background: #f0f4ff;
            border-left: 4px solid {accent};
            padding: 14px 16px;
            border-radius: 0 8px 8px 0;
            font-size: 14px;
            color: #3a4660;
            margin-bottom: 28px;
        }}

        /* News item headline */
        h2 {{
            font-size: 17px;
            font-weight: 700;
            color: #1a202c;
            margin-top: 32px;
            margin-bottom: 0;
            padding: 18px 20px 12px;
            background: #f8faff;
            border-top: 3px solid {accent};
            border-radius: 10px 10px 0 0;
        }}

        /* Card body: wraps everything between two h2s */
        h2 ~ p,
        h2 ~ ul,
        h2 ~ p.label,
        h2 ~ p.source {{
            background: #f8faff;
            padding: 0 20px;
        }}

        /* Last element in a card gets bottom rounding */
        h2 ~ *:last-child {{
            border-radius: 0 0 10px 10px;
            padding-bottom: 18px;
        }}

        /* Field labels: Overview, Developer Relevance etc. */
        p.label {{
            font-size: 11px;
            font-weight: 700;
            color: {accent};
            text-transform: uppercase;
            letter-spacing: 0.8px;
            margin-top: 14px;
            margin-bottom: 2px;
            padding: 0 20px;
            background: #f8faff;
            display: block;
        }}

        /* Regular paragraphs inside cards */
        p {{
            margin: 4px 0 10px;
            line-height: 1.75;
        }}

        /* Source lines */
        p.source {{
            font-size: 12px;
            color: #718096;
            font-style: italic;
            border-top: 1px solid #e2e8f0;
            margin-top: 12px;
            padding-top: 10px;
        }}

        /* Bullet lists */
        ul {{
            margin: 10px 0 10px 0;
            padding-left: 24px;
            background: #f8faff;
        }}
        li {{
            margin-bottom: 8px;
            line-height: 1.6;
        }}

        strong {{
            font-weight: 700;
            color: #1a202c;
        }}

        /* ── Footer ── */
        .footer {{
            text-align: center;
            padding: 20px 40px 28px;
            border-top: 1px solid #e8edf5;
            color: #a0aec0;
            font-size: 12px;
        }}

        /* ── DARK MODE ── */
        @media (prefers-color-scheme: dark) {{
            body {{
                background-color: #0f0f12 !important;
                background-image: none !important;
            }}
            .container {{
                background-color: #1a1a2e !important;
                border: 1px solid #2d2d44 !important;
            }}
            .email-header {{
                opacity: 0.95;
            }}
            .content {{
                color: #e2e8f0 !important;
                background-color: #1a1a2e !important;
            }}
            h2 {{
                color: #f0f4ff !important;
                background: #12122a !important;
            }}
            /* Card body: all paragraph blocks and lists inside card area */
            p.card-p, p.label, p.source, ul, li {{
                background: #12122a !important;
                color: #cbd5e0 !important;
            }}
            /* Summary intro block after h3 */
            h3 + p.card-p {{
                background: #1e1e38 !important;
                color: #a0b4d0 !important;
                border-left-color: {accent} !important;
            }}
            /* Ensure label accent color stays visible */
            p.label {{
                color: {accent} !important;
                opacity: 0.9;
            }}
            p.source {{
                color: #718096 !important;
                border-top-color: #2d2d44 !important;
            }}
            strong {{
                color: #e2e8f0 !important;
            }}
            .footer {{
                color: #4a5568 !important;
                border-top-color: #2d2d44 !important;
                background-color: #1a1a2e !important;
            }}
        }}

        /* Gmail dark mode overrides */
        [data-ogsc] .container, [data-ogsb] .container {{ background-color: #1a1a2e !important; }}
        [data-ogsc] .content, [data-ogsb] .content {{ color: #e2e8f0 !important; background-color: #1a1a2e !important; }}
        [data-ogsc] h2, [data-ogsb] h2 {{ color: #f0f4ff !important; background: #12122a !important; }}
        [data-ogsc] p.card-p, [data-ogsb] p.card-p {{ color: #cbd5e0 !important; background: #12122a !important; }}
        [data-ogsc] li, [data-ogsb] li {{ color: #cbd5e0 !important; background: #12122a !important; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="email-header">
            <h1>{title}</h1>
            <p class="subtitle">{subtitle}</p>
        </div>
        <div class="content">
            {formatted_content}
        </div>
        <div class="footer">
            <p>Powered by AI News Engine &nbsp;|&nbsp; &copy; Shubham Newsletter</p>
        </div>
    </div>
</body>
</html>"""


# ---------------------------------------------------------------------------
# Newsletter HTML (Master Prompt output)
# ---------------------------------------------------------------------------

def save_as_html(content, filename="news_report.html", return_content=False):
    """Saves the master-prompt news content as a styled HTML email file."""
    accent = "#667eea"
    header_bg = "linear-gradient(135deg, #667eea 0%, #764ba2 100%)"

    formatted_content = parse_markdown_to_html(content, accent_color=accent)
    html = _build_html_template(
        formatted_content=formatted_content,
        title="🚀 AI &amp; Tech News Brief",
        subtitle="Your curated digest of the latest developer-relevant AI developments",
        accent=accent,
        header_bg=header_bg,
    )

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Saved newsletter HTML → {filename}")

    if return_content:
        return html


# ---------------------------------------------------------------------------
# Radar HTML (Master Radar Prompt output)
# ---------------------------------------------------------------------------

def save_radar_html(content, filename="radar_report.html", return_content=False):
    """Saves the master-radar-prompt content as a styled HTML email file.

    Uses a distinct indigo/violet accent to visually differentiate
    from the standard newsletter.
    """
    accent = "#5a67d8"
    header_bg = "linear-gradient(135deg, #3c366b 0%, #5a67d8 100%)"

    formatted_content = parse_markdown_to_html(content, accent_color=accent)
    html = _build_html_template(
        formatted_content=formatted_content,
        title="📡 Emerging AI &amp; Dev Tool Radar",
        subtitle="Hidden gems &amp; low-visibility innovations — weekly scout report",
        accent=accent,
        header_bg=header_bg,
    )

    with open(filename, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ Saved radar HTML → {filename}")

    if return_content:
        return html