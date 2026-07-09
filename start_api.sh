#!/bin/bash
# start_api.sh — Arranca Katrix ERP API en el VPS
# Copiá este archivo al servidor y ejecutá: bash start_api.sh

set -e

# Ir a la carpeta de la API corregida
cd "$(dirname "$0")/api-crm"

# ─── Activar virtualenv ───────────────────────────────────────────────────────
if [ -d "../.venv" ]; then
    source ../.venv/bin/activate
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# ─── Instalar dependencias de la API ─────────────────────────────────────────
pip install -r requirements.txt -q
pip install python-dotenv -q

# ─── Arrancar ─────────────────────────────────────────────────────────────────
echo "🚀 Katrix ERP API arrancando en http://0.0.0.0:8000"
echo "📖 Documentación: http://0.0.0.0:8000/docs"
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 2 --env-file ../.env
