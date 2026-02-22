# RVTools Analyzer — Vibe

Uno strumento professionale per l'analisi e la visualizzazione degli export RVTools.

## Caratteristiche
- Analisi automatica di file `rvtools.xlsx`.
- Report HTML dettagliati con statistiche VM (Accese/Spente/Totale).
- Breakdown dei Sistemi Operativi con drill-down.
- Persistenza dei dati tramite bind mount.
- Interfaccia moderna basata sulle linee guida Var Group.

## Come avviare con Docker

### Utilizzando Docker Compose (Consigliato)
1. Clona il repository.
2. Avvia i container (scarica l'immagine o la costruisce localmente):
   ```bash
   docker-compose up -d
   ```
3. Accedi all'applicazione su `http://localhost:8080`.

Per fermare l'applicazione:
```bash
docker-compose down
```

I tuoi dati (uploads e report) verranno salvati nella cartella locale `./rvtools_data` grazie al volume configurato.

### Utilizzando Docker CLI
1. Costruisci l'immagine:
   ```bash
   docker build -t rvtools-vibe .
   ```
2. Avvia il container:
   ```bash
   docker run -d \
     -p 8080:8080 \
     -v $(pwd)/rvtools_data:/app/data \
     --name rvtools-analyzer \
     abeggi/rvtools-vibe:latest
   ```

## Migrazione su un altro server
Per spostare l'applicazione su un nuovo server:
1. Copia il file `docker-compose.yml`.
2. (Opzionale) Copia la cartella `rvtools_data` per mantenere lo storico dei report e le impostazioni.
3. Esegui `docker-compose up -d`. L'immagine verrà scaricata automaticamente da Docker Hub.

## Licenza
Proprietario - Var Group
