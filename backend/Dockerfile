FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose default port
EXPOSE 8000

# Bind host to 0.0.0.0 and use Render's dynamic $PORT (fallback 8000)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]