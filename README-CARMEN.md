# README de Carmen: frontend y fases 1–2

Qué hay hecho, qué falta y en qué punto se conecta la parte de cada compañero.

---

## 1. Estado actual

| Parte | Dueño | Estado |
|---|---|---|
| Frontend (React 18 + Vite) | Carmen | ✅ Funciona con datos **simulados** en JavaScript |
| Fase 1: `src/nlp/normalizacion.py` → `normalizar(texto)` | Carmen | ✅ Hecho + pruebas |
| Fase 2: `src/nlp/tokenizacion.py` → `tokenizar(texto)` | Carmen | ✅ Hecho + pruebas |
| Fase 3: `src/nlp/stopwords.py` → `quitar_stopwords(tokens)` | Fernando | ❌ Falta hacer |
| Fase 4: `src/nlp/lematizacion.py` → `lematizar(tokens)` y `stemmizar(tokens)` | Fernando | ❌ Falta hacer |
| Fases 1→4: `src/nlp/pipeline.py` → `TextPreprocessor`, `preprocesar_pasos(texto)` | Fernando | ❌ Falta hacer |
| Fase 5: vectorización + entidades + API FastAPI | Ramiro | En su rama `feat/crear_vectorizador-Backend-Ramiro-Fase-5` (no está en `main`) |
| Fase 6: modelo, `predict.py`, `metricas.json` | Jorge | ✅ Ya está en `main` (`src/models/`, `artifacts/metricas.json`) |

> Por ahora el frontend **no** usa el código en Python (ni el de Carmen, ni el de Ramiro, ni el de Jorge),
> porque el navegador solo puede usarlo a través de la API. Hasta que la API esté unida, todo lo que muestra sale de
> [`frontend/src/utils/nlpSimulator.js`](frontend/src/utils/nlpSimulator.js), un simulador en JS
> que imita el pipeline para poder probar la interfaz.

---

## 2. Cómo levantar el frontend

```powershell
cd frontend
npm install      # solo la primera vez
npm run dev
```

Se abre en **http://localhost:5173**.

---

## 3. Estructura del frontend

```
frontend/
├── index.html
├── package.json            # react, react-dom, lucide-react, vite
├── vite.config.js
└── src/
    ├── main.jsx
    ├── App.jsx                     # arma la página y llama a la API
    ├── api/client.js               # ⭐ ÚNICO punto de conexión con el backend
    ├── utils/nlpSimulator.js       # simulador JS (respaldo si la API no responde)
    ├── data/mockData.js            # productos de ejemplo del catálogo
    ├── assets/styles.css
    └── components/
        ├── Navbar.jsx              # [Colección 2026] [Inventario & Métricas] ⚡ Pipeline NLP
        ├── CatalogGrid.jsx / ProductCard.jsx   # catálogo de prendas
        ├── AssistantOrb.jsx        # orbe animado
        ├── ChatAssistant.jsx       # chat con el asistente
        ├── NlpPipelineDrawer.jsx   # panel "Cómo se procesa el texto" (pasos 1 a 6)
        └── AdminMetricsModal.jsx   # ventana de métricas (VACÍA, falta Jorge)
```

---

## 4. Mi parte (Carmen): fases 1 y 2

Ya están hechas, con las firmas de `docs/PLAN_DE_TRABAJO.md` (sección 3.3):

| Archivo | Función | Entra → sale |
|---|---|---|
| [`src/nlp/normalizacion.py`](src/nlp/normalizacion.py) | `normalizar(texto)` | `str → str` |
| [`src/nlp/tokenizacion.py`](src/nlp/tokenizacion.py) | `tokenizar(texto)` | `str → list[str]` (recibe el texto **ya normalizado**) |

**Normalización: qué se elimina y qué se conserva**

| Se elimina | Se conserva |
|---|---|
| Mayúsculas, tildes y diéresis (`á→a`, `ü→u`) | La **ñ** (`año` ≠ `ano`) |
| URLs, correos, menciones `@usuario` | **Números**: tallas (`32`) y precios (`100bs`) |
| Emojis y símbolos | Decimales (`12.50`; `12,50` pasa a `12.50`) |
| Puntuación `¿?¡!.,;:"()` | La barra en tallas (`s/m`) y el guion entre palabras (`talla-m`) |
| Apóstrofos: `jean's → jeans` | |

**Tokenización: casos difíciles del dominio**

| Entrada (normalizada) | Tokens |
|---|---|
| `talla-m` | `["talla", "m"]` |
| `xl` | `["xl"]` |
| `s/m` | `["s/m"]` |
| `100bs` | `["100", "bs"]` |
| `12.50` | `["12.50"]` |

**Uso (así lo encadena Fernando en `pipeline.py`):**
```python
from src.nlp.normalizacion import normalizar
from src.nlp.tokenizacion import tokenizar

tokens = tokenizar(normalizar("¿Tienen JEAN'S en Talla-M a 100Bs? 😍"))
# ['tienen', 'jeans', 'en', 'talla', 'm', 'a', '100', 'bs']
```

**Pruebas:** [`tests/test_normalizacion_tokenizacion.py`](tests/test_normalizacion_tokenizacion.py) (26 casos):
```powershell
python -m pytest tests/test_normalizacion_tokenizacion.py -v
```

> No creé `src/__init__.py` ni `src/nlp/__init__.py` porque Ramiro ya los trae en su rama; crearlos aquí
> daría conflicto al hacer el merge. Sin ellos los imports funcionan igual (Python 3 + `pytest.ini` con `pythonpath = .`).

En el frontend estos pasos se ven en **`NlpPipelineDrawer.jsx`**, en las secciones "1 Texto Original",
"2 Normalización" y "3 Tokenización". Leen `pasos.original`, `pasos.normalizado` y `pasos.tokens`.

---

## 5. Dónde se une la parte de Ramiro (Fase 5 + API)

**Qué hay que hacer:** hacer el merge de su rama a `main` con el PR de Ramiro y levantar su API:

```powershell
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000
```

**Cómo se conecta:** el frontend ya está preparado. [`frontend/src/api/client.js`](frontend/src/api/client.js) llama a:

| Endpoint | Para qué |
|---|---|
| `GET  http://localhost:8000/health` | ver si la API está viva |
| `POST http://localhost:8000/chat` con `{ texto, rol: "cliente" }` | respuesta del chat + pasos del pipeline |

Si la API responde, usa sus datos. Si no responde en 2,5 s, pasa solo al simulador en JS.
La URL se puede cambiar con la variable `VITE_API_URL`.

**Lo que el frontend espera que devuelva `/chat`** (coincide con `ChatResponse` de Ramiro en `api/schemas.py`):

```json
{
  "intencion": "consultar_stock",
  "probabilidad": 0.92,
  "entidades": { "talla": "32", "categoria": "jeans", "color": null, "fecha": "hoy" },
  "respuesta": "Tenemos el Slim Raw Denim en talla 32...",
  "pasos": {
    "original": "¿Qué jeans tienen en talla 32?",
    "normalizado": "que jeans tienen en talla 32",
    "tokens": ["que", "jeans", "tienen", "en", "talla", "32"],
    "sin_stopwords": ["jeans", "tienen", "talla", "32"],
    "lemas_o_raices": ["jean", "tener", "talla", "32"]
  }
}
```

⚠️ **Cosas a revisar al unir:**
- Las claves de entidades ya coinciden: `extraer_entidades` de Ramiro devuelve `talla, color, producto, categoria, fecha`, que es lo que lee el frontend. `producto` todavía no se muestra.
- CORS: su `src/config.yaml` ya permite `http://localhost:5173` en `api.cors.permitir_origenes`. Al unir `config.yaml`, hay que conservar esa parte.
- En el panel quedan marcados con **(Ramiro - Fase 5)**: "Entidades detectadas" y "TF-IDF (1,2) N-Grams" (`NlpPipelineDrawer.jsx`, líneas ~227 y ~255).
- Hoy `client.js` mezcla la lista de stop words eliminadas del simulador con la respuesta real (`fallback.stopWords.eliminadas`). Cuando la API devuelva las palabras eliminadas, hay que tomarlas de ahí.

---

## 6. Dónde se une la parte de Jorge (Fase 6: modelo y métricas)

**Lo que ya existe en `main`:**
- `src/models/predict.py` → `predecir(texto)` devuelve `{intencion, probabilidad, top3}`
- `src/models/train.py` → `python -m src.models.train` genera `artifacts/modelo.joblib` y `artifacts/metricas.json`
- `artifacts/metricas.json` → resultados del entrenamiento

**Puntos de unión:**

1. **Chat / intención:** la API de Ramiro (`/chat`) debe llamar a `predecir(texto)` de Jorge. El frontend recibe `intencion` y `probabilidad` por `/chat` y no necesita nada más.
   En `NlpPipelineDrawer.jsx` la sección "Intención & Modelo" muestra la intención y el top 3.

2. **Ventana de métricas** ([`AdminMetricsModal.jsx`](frontend/src/components/AdminMetricsModal.jsx)):
   - Ahora solo tiene el título: *"Métricas de Producción del Modelo — artifacts/metricas.json (Jorge - Fase 6)"*. El cuerpo está **vacío a propósito**.
   - Para llenarla:
     1. Que la API exponga `GET /metrics` (contrato en el plan, sección 3.4), que lea `artifacts/metricas.json`.
     2. En `client.js`, agregar una función `obtenerMetricas()` que haga `fetch(`${API_BASE_URL}/metrics`)`.
     3. En `AdminMetricsModal.jsx`, llamarla en un `useEffect` y mostrar los datos debajo de `.modal-header`: modelo ganador, F1 macro, accuracy, comparación LR vs Naive Bayes vs línea base y matriz de confusión.
   - Los estilos (`.kpi-grid`, `.metrics-table`, etc.) siguen en `src/assets/styles.css` y se pueden reutilizar.

3. **Valores inventados que hay que reemplazar:** en `NlpPipelineDrawer.jsx`, la línea de abajo del panel
   muestra `F1 Macro: 0.8622` y `Latencia: 8.4 ms` **fijos**. Hay que reemplazarlos por los datos reales de `/metrics` o borrarlos.

---

## 7. Checklist para unir todo

- [x] Carmen: `normalizacion.py` y `tokenizacion.py` (+ tests)
- [ ] Fernando: `stopwords.py` (fase 3) y `lematizacion.py` (fase 4)
- [ ] Fernando: `pipeline.py` con `TextPreprocessor` y `preprocesar_pasos(texto)` (usa `normalizar` → `tokenizar` de Carmen)
- [ ] Merge de la rama de Ramiro (PR revisado) → `/chat` usando `preprocesar_pasos` + `predecir` + `extraer_entidades`
- [ ] Jorge: `python -m src.models.train` para generar `artifacts/modelo.joblib`
- [ ] API: agregar `GET /metrics`
- [ ] Frontend: conectar `AdminMetricsModal.jsx` a `/metrics`; quitar el F1 y la latencia fijos
- [ ] Probar: `uvicorn api.main:app --port 8000` + `npm run dev`. En el chat **no** debería usarse el simulador (en `client.js`, `fromApi: true`)
