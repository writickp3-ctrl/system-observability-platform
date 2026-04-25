FROM python:3.10-slim

LABEL maintainer="Writick Parui"
LABEL description="System Observability Platform"

WORKDIR /app

# Install dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create required directories
RUN mkdir -p logs metrics sample_logs

EXPOSE 5000

# Use gunicorn for production
CMD ["gunicorn", "--workers=2", "--bind=0.0.0.0:5000", "--timeout=60", "--log-level=info", "app:app"]
