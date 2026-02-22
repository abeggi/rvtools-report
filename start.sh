#!/usr/bin/env bash
# Avvio di RVTools Analyzer sulla porta 6000
set -e
cd "$(dirname "$0")/app"
echo "🚀 Avvio RVTools Analyzer su http://0.0.0.0:8080 ..."
python3 app.py
