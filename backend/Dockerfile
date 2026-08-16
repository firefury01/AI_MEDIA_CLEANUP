FROM python:3.10-slim

WORKDIR /app

# System dependencies for OpenCV & Image processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render dynamically injects $PORT (default to 8000 if not set)
ENV PORT=8000

# Shell form use karna zaroori hai taaki $PORT expand ho sake
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"