# Proyecto_Topicos
Proyecto integrador de NLP y Machine Learning con API REST y frontend web.

## Estructura de carpetas

```text
Proyecto_Topicos/
├── backend/                 # API REST + pipeline NLP/ML (contenedor asistente-backend)
│   ├── api/                 # FastAPI: rutas, esquemas y servicios
│   ├── src/                 # Lógica de datos, NLP y ML
│   │   ├── data/            # Carga y validación de datos
│   │   ├── nlp/             # Procesamiento de texto (fases 1 a 5)
│   │   ├── models/          # Entrenamiento, evaluación e inferencia (fase 6)
│   │   └── config.yaml      # Parámetros de todo el sistema
│   ├── artifacts/           # Modelo entrenado y métricas
│   ├── notebooks/           # Análisis y experimentos
│   ├── tests/               # Pruebas con pytest
│   ├── requirements.txt
│   ├── Dockerfile
│   └── entrypoint.sh        # Entrena el modelo si falta y levanta la API
├── frontend/                # Aplicación web React + Vite (contenedor asistente-frontend)
│   ├── src/
│   │   ├── api/             # Comunicación con el backend
│   │   └── components/      # Componentes de la interfaz
│   ├── Dockerfile
│   └── nginx.conf
├── database/                # Datos del sistema
│   ├── raw/                 # Dataset de intenciones y tienda demo
│   ├── processed/           # Datos preparados
│   ├── ood_val.csv          # Consultas fuera de dominio (calibración)
│   ├── ood_test.csv         # Consultas fuera de dominio (prueba)
│   └── tienda.db            # Base de datos SQLite de la tienda (se genera)
├── docs/                    # Documentación técnica
├── .github/workflows/       # Verificaciones automáticas
└── docker-compose.yml       # Levanta backend y frontend
```

## Ejecución con Docker

```bash
docker compose up --build
```

- Frontend: http://localhost:5173
- API y documentación: http://localhost:8000/docs

Más detalles en [docs/DOCKER.md](docs/DOCKER.md).

## Ejecución local (sin Docker)

Requiere Python 3.11 o superior y Node 18 o superior.

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate          # En Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
python -m src.models.train      # Genera artifacts/modelo.joblib y artifacts/metricas.json
python -m pytest
uvicorn api.main:app --reload

# Frontend (en otra terminal)
cd frontend
npm install
npm run dev
```
