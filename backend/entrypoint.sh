#!/bin/sh
# Arranque del backend: entrena el modelo si todavía no existe y luego levanta la API.
set -e

if [ ! -f artifacts/modelo.joblib ]; then
  echo "[entrypoint] No existe artifacts/modelo.joblib: entrenando con python -m src.models.train ..."
  if ! python -m src.models.train; then
    echo "[entrypoint] ERROR: el entrenamiento falló. La API arranca sin modelo (revisar GET /health)."
  fi
fi

exec uvicorn api.main:app --host 0.0.0.0 --port 8000
