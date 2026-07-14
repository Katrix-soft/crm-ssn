#!/bin/bash
# Matar procesos en puertos 18000 y 1430 por si acaso
fuser -k 18000/tcp || true
fuser -k 1430/tcp || true

echo "Starting backend..."
cd "/home/nachin/Documentos/katrix/productor de seguros/api-crm"
../.venv/bin/python -m uvicorn api:app --host 127.0.0.1 --port 18000 --env-file .env > backend.log 2>&1 &
BACKEND_PID=$!

echo "Starting frontend..."
cd "/home/nachin/Documentos/katrix/productor de seguros/desktop-tauri/src"
python3 -m http.server 1430 --bind 127.0.0.1 > frontend.log 2>&1 &
FRONTEND_PID=$!

echo "Servers started. Backend PID: $BACKEND_PID, Frontend PID: $FRONTEND_PID"
sleep 3
cat "/home/nachin/Documentos/katrix/productor de seguros/api-crm/backend.log"
cat "/home/nachin/Documentos/katrix/productor de seguros/desktop-tauri/src/frontend.log"

# Mantener vivo el script
wait
