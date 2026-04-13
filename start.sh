#!/usr/bin/env bash
# Manager per RVTools Analyzer

# Ottieni il percorso assoluto della cartella dello script
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$SCRIPT_DIR/app"
PID_FILE="$SCRIPT_DIR/app.pid"
LOG_FILE="$SCRIPT_DIR/app.log"

case "$1" in
  start)
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
      echo "⚠️  L'app è già in funzione (PID: $(cat "$PID_FILE"))."
    else
      cd "$APP_DIR"
      echo "🚀 Avvio RVTools Analyzer su http://0.0.0.0:8080 ..."
      # Avvio in background, l'output va nel log nella root del progetto
      python3 app.py > "$LOG_FILE" 2>&1 &
      echo $! > "$PID_FILE"
      echo "✅ Avviato con PID $(cat "$PID_FILE")."
    fi
    ;;
  stop)
    if [ -f "$PID_FILE" ]; then
      PID=$(cat "$PID_FILE")
      if kill -0 $PID 2>/dev/null; then
        echo "🛑 Fermando RVTools Analyzer (PID: $PID)..."
        kill $PID && rm "$PID_FILE"
        echo "✅ Fermato."
      else
        echo "⚠️  Il processo $PID non è più in esecuzione. Rimuovo il file .pid."
        rm "$PID_FILE"
      fi
    else
      echo "⚠️  Nessun file .pid trovato. Provo a terminare processi residui..."
      pkill -f "python3 app.py" && echo "✅ Processi terminati." || echo "❌ Nessun processo trovato."
    fi
    ;;
  restart)
    $0 stop
    sleep 2
    $0 start
    ;;
  status)
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
      echo "🟢 In funzione con PID $(cat "$PID_FILE")."
    else
      echo "🔴 Non in funzione."
    fi
    ;;
  *)
    # Default behavior: foreground execution (compatible with previous behavior)
    cd "$APP_DIR"
    echo "🚀 Avvio RVTools Analyzer (foreground) su http://0.0.0.0:8080 ..."
    python3 app.py
    ;;
esac
