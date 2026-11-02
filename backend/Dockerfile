# Imagen del backend: API FastAPI + pipeline NLP/ML (fases 1 a 6)
# Python 3.12 porque las versiones fijadas en requirements.txt exigen Python >= 3.11
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Dependencias primero, para que Docker reutilice esta capa si solo cambia el código
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

COPY entrypoint.sh /entrypoint.sh
# Quita los finales de línea de Windows (CRLF) para que el script corra en Linux
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
