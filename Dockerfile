FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Install system dependencies if needed (e.g., for pandas/numpy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ /app/

# Environment variables
ENV DATA_DIR=/app/data
ENV FLASK_APP=app:app
ENV PYTHONUNBUFFERED=1

# Create data directory and subdirectories
RUN mkdir -p /app/data/uploads /app/data/reports

# Expose the application port
EXPOSE 8080

# Command to run the application using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "app:app"]
