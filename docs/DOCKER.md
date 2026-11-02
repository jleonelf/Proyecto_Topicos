# Ejecutar el sistema con Docker

Levanta el sistema completo (base de datos, API con el modelo y frontend) con un solo comando, sin instalar Python, Node ni PostgreSQL en la máquina.

## Requisitos

- Docker Desktop encendido (incluye Docker Compose).

## Organización

| Carpeta | Qué contiene | Contenedor | Acceso |
|---|---|---|---|
| `database/` | Esquema SQL, dataset de intenciones, conjuntos OOD y tienda demo | `asistente-db` (PostgreSQL 16) | `localhost:5433` |
| `backend/` | API FastAPI, pipeline NLP/ML, modelo entrenado | `asistente-backend` | http://localhost:8000/docs |
| `frontend/` | Aplicación React + Vite, servida con Nginx | `asistente-frontend` | http://localhost:5173 |

Orden de arranque: `db` → `backend` (espera a que PostgreSQL esté listo) → `frontend`.

## Base de datos

- Motor: PostgreSQL 16. Base `tienda`, usuario `tienda`, contraseña `tienda` (solo para desarrollo local).
- Tablas: `productos`, `ventas` y `tienda`, con el formato estándar de importación del plan (sección 3.2). Las define [database/init/01_esquema.sql](../database/init/01_esquema.sql), que PostgreSQL ejecuta solo la primera vez que se crea el volumen `datos_postgres`.
- El backend se conecta con la variable `DATABASE_URL` mediante `backend/src/data/conexion.py`. Sin esa variable (ejecución sin Docker) usa SQLite en `database/tienda.db`.
- Se puede abrir con cualquier cliente (pgAdmin, DBeaver) en `localhost:5433`, o desde la terminal:

```bash
docker compose exec db psql -U tienda -d tienda
# dentro de psql: \dt para listar tablas, SELECT * FROM productos;
```

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

# Detener y borrar los datos de PostgreSQL (vuelve a crear las tablas al levantar)
docker compose down -v
```

La primera vez que arranca, el backend ejecuta `python -m src.models.train` porque todavía no existe `backend/artifacts/modelo.joblib`. Si el entrenamiento falla, la API arranca igual y `GET /health` muestra `modelo_cargado: false`.

## Modificaciones en vivo (defensa)

Las carpetas `backend/` y `database/` están montadas dentro del contenedor del backend, así que los cambios hechos en la máquina se ven dentro sin reconstruir la imagen:

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
