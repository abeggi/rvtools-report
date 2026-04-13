# RVTools Analyzer — Vibe

Uno strumento professionale per l'analisi e la visualizzazione degli export RVTools.

## Caratteristiche
- Analisi automatica di file `rvtools.xlsx`.
- Report HTML interattivi con statistiche VM dettagliate (Accese/Spente/Totale).
- **Export PDF professionale** con branding aziendale e layout ottimizzato.
- Breakdown dei Sistemi Operativi con drill-down e raggruppamento intelligente.
- Impostazioni personalizzabili (Logo, Colori, Nome Azienda).
- Interfaccia moderna responsive basata sulle linee guida Var Group.

## Installazione su Host (Linux)

### 1. Installazione dipendenze di sistema
L'applicazione richiede alcune librerie per l'elaborazione dei dati e la generazione dei PDF (WeasyPrint):

```bash
sudo apt-get update && sudo apt-get install -y \
    python3-pip python3-venv \
    build-essential python3-dev libffi-dev \
    libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libpangocairo-1.0-0 \
    libglib2.0-0 libgobject-2.0-0 libcairo2 libfontconfig1 \
    libjpeg-dev libopenjp2-7-dev shared-mime-info fonts-liberation
```

### 2. Configurazione applicazione
1. Clona il repository nella cartella desiderata (es: `/rvtools-report`).
2. Installa le dipendenze Python:
   ```bash
   pip3 install -r requirements.txt
   ```
3. Crea la cartella per i dati:
   ```bash
   mkdir -p rvtools_data
   ```

### 3. Avvio manuale
Puoi avviare l'app per testarla con:
```bash
export DATA_DIR=$(pwd)/rvtools_data
cd app
gunicorn --bind 0.0.0.0:8080 app:app
```

## Configurazione come Servizio (Systemd)

Per far girare l'applicazione automaticamente all'avvio:

1. Copia il file di servizio:
   ```bash
   sudo cp rvtools-analyzer.service /etc/systemd/system/
   ```
2. Ricarica systemd e abilita il servizio:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable rvtools-analyzer
   sudo systemctl start rvtools-analyzer
   ```
3. Verifica lo stato:
   ```bash
   sudo systemctl status rvtools-analyzer
   ```

## Note Tecniche
- L'esportazione PDF utilizza **WeasyPrint**. Se il layout appare sfasato, verifica che i font (fonts-liberation) siano installati correttamente.
- I dati caricati e i report generati vengono salvati nella cartella definita da `DATA_DIR` (default: `rvtools_data`).
