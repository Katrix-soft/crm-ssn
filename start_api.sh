#!/bin/bash
# start_api.sh — Arranca Katrix ERP API en el VPS
# Copiá este archivo al servidor y ejecutá: bash start_api.sh

set -e

# Ir a la carpeta de la API corregida
cd "$(dirname "$0")/api-crm"

# ─── Variables de entorno (editá antes de deployar) ──────────────────────────
export KATRIX_SECRET_KEY="reemplaza-con-una-clave-segura-de-64-chars"
export TOKEN_EXPIRE_HOURS="24"
# Reemplazá con tu dominio real (Flutter web o IP del VPS)
export KATRIX_CORS_ORIGINS="https://tuapp.com,http://tuip.com,http://localhost"

# ─── Activar virtualenv ───────────────────────────────────────────────────────
if [ -d "../.venv" ]; then
    source ../.venv/bin/activate
elif [ -d "../venv" ]; then
    source ../venv/bin/activate
fi

# ─── Instalar dependencias de la API ─────────────────────────────────────────
pip install -r requirements.txt -q

# ─── Arrancar ─────────────────────────────────────────────────────────────────
echo "🚀 Katrix ERP API arrancando en http://0.0.0.0:8000"
echo "📖 Documentación: http://0.0.0.0:8000/docs"
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 2
