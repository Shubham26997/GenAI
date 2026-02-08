# Use a slim Python image for efficiency
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install dependencies first (better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Default environment variables
ENV TIME_FRAME=7
ENV LOAD_FROM_CACHE=false

# Run the newsletter core script
CMD ["python", "core.py"]
