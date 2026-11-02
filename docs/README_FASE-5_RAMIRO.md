# Fase 5: vectorización y backend (Ramiro)

Esta rama contiene la implementación de la **Fase 5 de NLP (Vectorización TF-IDF y N-gramas)**, el **extractor de entidades** y la **capa completa del Backend (API REST con FastAPI)**. Incluye el módulo de vectorización `src/nlp/vectorizacion.py`, el extractor `src/nlp/entidades.py`, los controladores y servicios de la API en `api/`, el cuaderno de experimentos `notebooks/02c_vectorizacion.ipynb`, la suite completa de pruebas unitarias (`tests/`) y los contratos de configuración en `src/config.yaml`.

## Dependencias de integración

En el pipeline de NLP y modelado, el entrenamiento de Jorge (`src.models.train`) importa `src.nlp.vectorizacion.crear_vectorizador(config)` para ensamblar el vectorizador dentro del `Pipeline` reproducible de scikit-learn.

En el backend:
- `api/services/chat_service.py` carga el artefacto serializado `artifacts/modelo.joblib` (generado por Jorge). Para garantizar el desacoplamiento y no bloquear el desarrollo del frontend ni las pruebas de integración, el servicio cuenta con un clasificador heurístico de contingencia sobre las 13 intenciones que opera si el archivo `.joblib` aún no existe en disco.
- `api/services/reportes_service.py` consulta la base de datos `artifacts/tienda.db` (generada por Carmen mediante `src.data.importador`). Si la base de datos aún no ha sido importada, provee datos estructurados de referencia para que el panel administrativo del frontend funcione desde el primer día.
- `src/config.yaml` es el archivo de contrato compartido. En esta rama define las secciones:
  - `vectorizador:` parámetros de TF-IDF (`ngram_range: [1, 2]`, `min_df: 1`, `max_df: 0.95`, `sublinear_tf: true`, `norm: "l2"`).
  - `api:` puerto, host, configuración de CORS para el frontend (`http://localhost:5173`), `umbral_confianza: 0.60` y validaciones de longitud (mínimo 3 y máximo 500 caracteres).

## Instalación y ejecución tras integrar las dependencias

```bash
# 1. Crear y activar entorno virtual
python -m venv .venv
.venv\Scripts\activate       # En Windows
# source .venv/bin/activate  # En Linux/macOS

# 2. Instalar dependencias fijadas
pip install -r requirements.txt

# 3. Ejecutar las pruebas automatizadas (41 pruebas de vectorización, entidades y API)
python -m pytest -v

# 4. Levantar el servidor Backend en modo desarrollo
uvicorn api.main:app --reload --port 8000
```

Con el servidor en ejecución, la documentación interactiva Swagger se encuentra disponible en `http://localhost:8000/docs` y el diagnóstico en `http://localhost:8000/health`.

### Comprobación rápida de endpoints mediante cURL o terminal

```bash
# Diagnóstico de salud y artefactos
curl http://localhost:8000/health

# Inferencia directa de intención y Top 3
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" -d "{\"texto\": \"¿tienen jeans negros en talla 32?\"}"

# Chat interactivo con extracción de entidades y umbral de confianza
curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d "{\"texto\": \"¿tienen stock de polera blanca en talla M?\", \"rol\": \"cliente\"}"

# Consulta de métricas del modelo
curl http://localhost:8000/metrics

# Reporte administrativo de stock bajo
curl http://localhost:8000/reportes/stock_bajo
```

## Componentes y resultados técnicos

### 1. Vectorización (Fase 5 - NLP)
Implementada en `src/nlp/vectorizacion.py`. Se seleccionó **TF-IDF con unigramas y bigramas `(1, 2)`** y escala logarítmica sublineal (`sublinear_tf=True`), normalizada con norma $L_2$.
- **Justificación de bigramas:** Capturan el contexto inmediato imprescindible en el comercio de ropa (*"talla m"*, *"talla 32"*, *"sin stock"*, *"envío gratis"*), incrementando la discriminación frente a unigramas aislados.
- En la validación cruzada estratificada sobre el corpus de intenciones (5 folds), la Regresión Logística con unigramas y bigramas `(1, 2)` alcanzó un $F_1$-Macro de referencia de **0,938**, superando a la variante con solo unigramas (**0,891**) y a Complement Naive Bayes (**0,908**).

### 2. Extractor de Entidades
Implementado en `src/nlp/entidades.py`. Detecta heurísticamente y normaliza:
- **Tallas:** Alfabéticas (`XS`, `S`, `M`, `L`, `XL`, `XXL`), compuestas (`S/M`, `M/L`) y numéricas (`28` a `52`).
- **Colores:** Mapeo y lematización a masculino singular canónico (*"negras"* $\rightarrow$ `negro`, *"azules"* $\rightarrow$ `azul`, *"café"*).
- **Prendas y categorías:** Catálogo base de ropa con soporte dinámico para catálogos importados de la tienda (`catalogo={"productos": [...]}`).
- **Fechas:** Expresiones temporales para reportes administrativos (*"hoy"*, *"esta semana"*, *"octubre"*, formatos ISO).

### 3. API REST (FastAPI)
- **Validación temprana con Pydantic:** Todo texto de entrada pasa por validadores de campo en `api/schemas.py`. Si una consulta está vacía, contiene solo espacios o supera los 500 caracteres, la API responde con código **HTTP 422 Unprocessable Content** y un mensaje explicativo en español.
- **Control de Umbral de Confianza (`0.60`):** En `POST /chat`, si la probabilidad de la intención predicha es menor a 0,60, el sistema responde marcando la intención como `desconocido` y solicita amablemente reformular la consulta.
- **Endpoints cubiertos:** `GET /`, `GET /health`, `POST /predict`, `POST /chat`, `GET /metrics`, `GET /reportes/{tipo}`, `POST /predict/lote` (vía JSON y archivo `.txt`/`.csv`), `POST /tienda/importar`.

## Cuaderno de experimentos (`notebooks/02c_vectorizacion.ipynb`)

El notebook documenta la justificación matemática de TF-IDF, la comparativa cuantitativa de vocabulario de unigramas vs. bigramas, el análisis de `min_df` y `sublinear_tf`, la evaluación empírica con clasificadores y la comparativa teórica/práctica entre TF-IDF y Embeddings.

Para visualizarlo o reejecutarlo:
- Abrir directamente en VS Code / Jupyter Notebook y presionar *"Run All"*.
- O ejecutar desatendido mediante:
  ```bash
  python -m jupyter nbconvert --to notebook --execute --inplace notebooks/02c_vectorizacion.ipynb
  ```
