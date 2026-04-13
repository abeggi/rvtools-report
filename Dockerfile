FROM python:3.11-slim

# Imposta la directory di lavoro
WORKDIR /app

# Installa le dipendenze di sistema
# build-essential e python3-dev sono utili per pacchetti che richiedono compilazione
# weasyprint richiede pango, cairo e altre librerie grafiche per la generazione dei PDF
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libffi-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libpangocairo-1.0-0 \
    libglib2.0-0 \
    libgobject-2.0-0 \
    libcairo2 \
    libfontconfig1 \
    libjpeg-dev \
    libopenjp2-7-dev \
    shared-mime-info \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# Copia i requisiti e installa le dipendenze Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice dell'applicazione
COPY app/ /app/

# Variabili d'ambiente
ENV DATA_DIR=/app/data
ENV FLASK_APP=app:app
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Crea le directory per i dati se non esistono
RUN mkdir -p /app/data/uploads /app/data/reports

# Espone la porta dell'applicazione
EXPOSE 8080

# Comando per avviare l'applicazione con Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "app:app"]
