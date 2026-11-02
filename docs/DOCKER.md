# Ejecutar el sistema con Docker

Levanta el sistema completo (frontend, API y modelo) con un solo comando, sin instalar Python ni Node en la máquina.

## Requisitos

- Docker Desktop encendido (incluye Docker Compose).

## Organización

| Carpeta | Qué contiene | Contenedor | URL |
|---|---|---|---|
| `backend/` | API FastAPI, pipeline NLP/ML, modelo entrenado | `asistente-backend` | http://localhost:8000/docs |
| `frontend/` | Aplicación React + Vite, servida con Nginx | `asistente-frontend` | http://localhost:5173 |
| `database/` | Dataset de intenciones, conjuntos OOD, tienda demo y `tienda.db` | montada en el backend como `/database` | — |

**Base de datos:** el proyecto usa SQLite (`database/tienda.db`), una base de datos en un solo archivo que no necesita un servidor aparte. Por eso no tiene contenedor propio: la carpeta `database/` se monta dentro del contenedor del backend, que es quien la lee y la escribe. Así los datos quedan en la carpeta del proyecto y no se pierden al borrar los contenedores.

## Uso

```bash
# Construir y levantar todo (la primera vez tarda varios minutos)
docker compose up --build

# Levantar en segundo plano
docker compose up -d

# Ver los registros del backend (entrenamiento y API)
docker compose logs -f backend

# Detener
docker compose down
```

La primera vez que arranca, el backend ejecuta `python -m src.models.train` porque todavía no existe `backend/artifacts/modelo.joblib`. Si el entrenamiento falla, la API arranca igual y `GET /health` muestra `modelo_cargado: false`.

## Modificaciones en vivo (defensa)

Las carpetas `backend/` y `database/` están montadas dentro del contenedor, así que los cambios hechos en la máquina se ven dentro sin reconstruir la imagen:

```bash
# 1. Editar backend/src/config.yaml (por ejemplo ngram_range, C, alpha o modo lema/stem),
#    el código de backend/src/ o agregar frases a database/raw/intenciones.csv
# 2. Reentrenar dentro del contenedor
docker compose exec backend python -m src.models.train
# 3. Revisar las métricas nuevas (también quedan en backend/artifacts/metricas.json)
docker compose exec backend cat artifacts/metricas.json
```

La API detecta el modelo nuevo y lo recarga en la siguiente consulta. Si se cambia código de `backend/api/`, hay que reiniciar el backend: `docker compose restart backend`.

Los cambios en `requirements.txt` requieren reconstruir: `docker compose up --build backend`.

Los cambios en `frontend/` requieren reconstruir el frontend: `docker compose up --build frontend`.

## Pruebas dentro del contenedor

```bash
docker compose exec backend python -m pytest
```
