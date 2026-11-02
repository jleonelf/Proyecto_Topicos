# Plan de trabajo – Asistente para tiendas de ropa

**Equipo:** Carmen · Fernando · Jorge · Ramiro
**Entrega:** **lunes 2 de noviembre, 23:59** (tag `entrega-final`) · **Presentación:** martes 3 de noviembre
**Última actualización:** 29 de octubre de 2026

Las 6 fases de NLP y ML se reparten entre los cuatro, así todos tienen commits propios en NLP o ML (el PDF lo exige porque a todos nos van a preguntar sobre eso). Además, cada uno es dueño de una capa del sistema.

---

## 1. Idea del producto: cómo funciona para cualquier tienda

Un asistente que responde a **clientes** (stock, precios, tallas, envíos, devoluciones) y al **área administrativa** (reportes de ventas, más vendidos, stock bajo), por texto y por voz.

La clave para que sirva a cualquier tienda es separar lo que se **entrena** de lo que se **importa**:

| Parte | ¿Se entrena? | Depende de la tienda | Qué es |
|---|---|---|---|
| Clasificador de intenciones | Sí | No | Frases genéricas ("¿tienen esto en talla M?") → intención. Sirve igual para cualquier tienda de ropa. |
| Datos de la tienda | No, se importan | Sí | CSV con formato estándar (productos, ventas, información de la tienda). Se consultan para armar la respuesta. |
| Extractor de entidades | No (reglas + NLP) | Usa el catálogo importado | Detecta talla, color, categoría, producto y fechas en la frase. |
| Respuestas | No | Sí | Plantillas por intención rellenadas con los datos importados. |

Flujo de una consulta:

```
texto o voz (navegador)
  → API /chat
  → pipeline NLP (normalizar → tokens → stop words → lemas → TF-IDF)
  → modelo → intención + probabilidad      (si prob < umbral → "no entendí")
  → extractor de entidades (talla, color, producto, fechas)
  → consulta a los datos importados de la tienda
  → respuesta en texto → el navegador la lee en voz alta
```

> Opcional: el script de entrenamiento acepta un archivo extra con frases propias de una tienda para reentrenar, pero el modelo base ya funciona sin él.

---

## 2. Reparto de las 6 fases

| # | Fase | Responsable | Qué entrega | Qué compara o justifica |
|---|---|---|---|---|
| 1 | Normalización | **Carmen** | `src/nlp/normalizacion.py` → `normalizar(texto)` | Qué se elimina y qué se conserva: minúsculas, tildes, puntuación, números (¿se conservan tallas como "32"?), URLs, emojis |
| 2 | Tokenización | **Carmen** | `src/nlp/tokenizacion.py` → `tokenizar(texto)` | Casos difíciles del dominio: "talla-M", "xl", "s/m", "100bs", "jean's" |
| 3 | Stop words | **Fernando** | `src/nlp/stopwords.py` → `quitar_stopwords(tokens)` | Lista en español; por qué se quitan "no", "sin", "más" de la lista y se agregan "porfa", "oye" |
| 4 | Lematización (y stemming) | **Fernando** | `src/nlp/lematizacion.py` → `lematizar(tokens)` y `stemmizar(tokens)` | Implementar los dos y comparar métricas para elegir uno |
| 5 | TF-IDF / embeddings | **Ramiro** | `src/nlp/vectorizacion.py` → `crear_vectorizador(config)` | Unigramas vs unigramas + bigramas; `max_features`, `min_df`, `max_df` documentados; opcional: TF-IDF vs embeddings |
| 6 | Modelo | **Jorge** | `src/models/train.py`, `src/models/predict.py` | Regresión logística vs Naive Bayes vs línea base; validación cruzada; análisis de errores |

**Quién junta las fases:** Fernando arma `src/nlp/pipeline.py` con `TextPreprocessor`, la clase que encadena las fases 1→4 y va dentro del modelo guardado. Su fase es la última de limpieza de texto, así que es quien recibe todo.

Cada fase muestra **un ejemplo antes/después** y su justificación en el notebook de su responsable.

### Capa del sistema de cada uno

| Integrante | Fases de NLP/ML | Capa del sistema | Notebook propio |
|---|---|---|---|
| **Carmen** | 1. Normalización · 2. Tokenización | Datos: dataset de intenciones, tienda demo, importador, EDA, división estratificada · Panel admin del frontend | `01_eda.ipynb`, `02a_normalizacion_tokenizacion.ipynb` |
| **Fernando** | 3. Stop words · 4. Lematización | Frontend: chat, voz y vista del preprocesamiento paso a paso | `02b_stopwords_lematizacion.ipynb` |
| **Ramiro** | 5. TF-IDF / embeddings | Backend: API, extractor de entidades y pruebas | `02c_vectorizacion.ipynb` |
| **Jorge** | 6. Modelo | Pipeline reproducible: script de entrenamiento, artefactos, métricas, `requirements.txt` | `03_modelos.ipynb` |

> Un notebook por persona evita conflictos de merge (los `.ipynb` se mezclan muy mal en Git).

### Cómo trabajar en paralelo si las fases van en cadena

Las fases dependen una de otra, pero nadie espera a nadie:
- Desde el día 1 cada uno usa un **reemplazo simple** de la fase anterior (por ejemplo, `texto.lower().split()` en lugar de `tokenizar`) y lo cambia por la función real cuando se integra.
- Lo único que hay que respetar es la **firma de las funciones** de la sección 3.3.

### Modelo recomendado (fase 6)

**Regresión logística** como candidato a producción y **Naive Bayes** (`ComplementNB` o `MultinomialNB`) como comparación, más la línea base de clase más frecuente.

Por qué regresión logística:

| Característica del proyecto | Por qué le sirve la regresión logística |
|---|---|
| Frases cortas vectorizadas con TF-IDF, con miles de columnas casi todas en cero | Los modelos lineales funcionan muy bien con este tipo de datos; es la combinación clásica para clasificar texto |
| Unas 1.000–1.300 frases y 13 intenciones | Funciona bien con pocos datos y no se sobreajusta fácilmente si se regula `C` |
| Umbral de confianza ("si la probabilidad es menor que el umbral, no entendí") | Da probabilidades confiables, y el chatbot las necesita |
| Defensa oral | Es interpretable: se puede mostrar qué palabras empujan hacia cada intención (por ejemplo, "talla", "hay" o "tienen" → `consultar_stock`) |
| Modificación en vivo | Entrena en segundos, así que reentrenar frente al docente no es un problema |

Por qué Naive Bayes como comparación: es el otro clásico para texto, es muy rápido, rinde bien con pocos datos y es fácil de explicar (cuenta con qué probabilidad aparece cada palabra en cada intención y aplica el teorema de Bayes). `ComplementNB` maneja mejor las intenciones con menos frases. Lo esperable es que la regresión logística gane por poco en F1 macro, porque no asume que las palabras son independientes.

Por qué no los demás:

| Modelo | Problema para este caso |
|---|---|
| KNN | En TF-IDF con miles de dimensiones las distancias pierden sentido, y es lento para predecir |
| Árbol de decisión | Se sobreajusta con texto disperso y pocos datos |
| Random Forest / XGBoost | Pueden funcionar, pero rinden menos con TF-IDF disperso, tardan más en la validación cruzada y cuesta más explicar sus decisiones |
| K-means | No es supervisado; nosotros sí tenemos etiquetas |
| Regresión lineal | Predice un número, no una clase |

Validación cruzada estratificada de 5 partes, con F1 macro como métrica (castiga que el modelo falle en las intenciones con pocas frases):

```python
# Regresión logística
{"modelo__C": [0.1, 1, 10], "modelo__class_weight": [None, "balanced"]}

# Naive Bayes
{"modelo__alpha": [0.1, 0.5, 1.0]}
```

> La regresión logística es la apuesta inicial, pero **queda en producción el modelo que gane en las métricas**, y esa comparación se documenta en el informe (el PDF pide justificar la elección con métricas).

---

## 3. Acuerdos del día 1 (contratos entre fases y capas)

Esto se acuerda **hoy** para que los cuatro puedan trabajar en paralelo sin esperarse.

### 3.1 Intenciones

| Rol | Intención | Ejemplo |
|---|---|---|
| cliente | `saludo` | "hola, buenas tardes" |
| cliente | `despedida` | "gracias, eso era todo" |
| cliente | `consultar_stock` | "¿tienen jeans negros en talla 32?" |
| cliente | `consultar_precio` | "¿cuánto cuesta la chaqueta de cuero?" |
| cliente | `consultar_tallas` | "¿qué tallas hay de esta polera?" |
| cliente | `envios` | "¿hacen envíos a provincia?" |
| cliente | `devoluciones` | "quiero cambiar una prenda" |
| cliente | `horarios_ubicacion` | "¿a qué hora abren?" |
| cliente | `metodos_pago` | "¿aceptan QR?" |
| admin | `reporte_ventas` | "dame las ventas de esta semana" |
| admin | `productos_mas_vendidos` | "¿qué fue lo más vendido en octubre?" |
| admin | `stock_bajo` | "¿qué productos se están acabando?" |
| admin | `ventas_por_categoria` | "ventas por categoría del mes" |
| cliente | `recomendar_productos` | "¿qué me recomiendas?" (agregada el 2 de noviembre: el modelo respondía "no entendí" a estas preguntas) |

Meta: **80 a 100 frases por intención** (≈ 1.000–1.300 en total), en español y con variedad (errores de tipeo, sin tildes, informal, con emojis). Carmen coordina el dataset, pero **todos aportan frases** el primer día para llegar rápido a la meta.

### 3.2 Formatos de archivo

`data/raw/intenciones.csv` — dataset de entrenamiento:

```csv
texto,intencion,rol,fuente
"tienen jeans en talla 32?",consultar_stock,cliente,manual
```

`fuente` = `manual` | `parafraseo` | `ia` (para documentar el origen; si usamos IA se declara en el informe).

Formato estándar para importar **cualquier tienda** (`data/raw/tienda_demo/` trae una tienda de ejemplo):

| Archivo | Columnas |
|---|---|
| `productos.csv` | `sku, nombre, categoria, talla, color, precio, stock` |
| `ventas.csv` | `fecha (YYYY-MM-DD), sku, cantidad, precio_unitario` |
| `tienda.json` | `nombre, direccion, horarios, envios, devoluciones, metodos_pago` |

### 3.3 Firmas de las funciones

| Fase / capa | Módulo | Función / clase | Entra → sale | Dueño |
|---|---|---|---|---|
| 1 | `src/nlp/normalizacion.py` | `normalizar(texto)` | `str → str` | Carmen |
| 2 | `src/nlp/tokenizacion.py` | `tokenizar(texto)` | `str → list[str]` | Carmen |
| 3 | `src/nlp/stopwords.py` | `quitar_stopwords(tokens)` | `list[str] → list[str]` | Fernando |
| 4 | `src/nlp/lematizacion.py` | `lematizar(tokens)`, `stemmizar(tokens)` | `list[str] → list[str]` | Fernando |
| 1→4 | `src/nlp/pipeline.py` | `TextPreprocessor` (transformer de scikit-learn) y `preprocesar_pasos(texto) -> dict` (cada paso, para el frontend) | `str → str` | Fernando |
| 5 | `src/nlp/vectorizacion.py` | `crear_vectorizador(config)` | devuelve un `TfidfVectorizer` configurado | Ramiro |
| 6 | `src/models/train.py` | `python -m src.models.train` | datos crudos → `artifacts/modelo.joblib`, `artifacts/metricas.json` | Jorge |
| 6 | `src/models/predict.py` | `predecir(texto)` | `str → {intencion, probabilidad, top3}` | Jorge |
| Datos | `src/data/dataset.py` | `cargar_intenciones()`, `dividir(df, seed=42)` (estratificado) | | Carmen |
| Datos | `src/data/importador.py` | `importar_tienda(carpeta)` → valida columnas y carga a `artifacts/tienda.db` (SQLite) | | Carmen |
| Backend | `src/nlp/entidades.py` | `extraer_entidades(texto, catalogo)` | `str → {talla, color, categoria, producto, fechas}` | Ramiro |
| Todos | `src/config.yaml` | Parámetros: `modo` (lema/stem), stop words extra, `ngram_range`, `min_df`, `max_df`, `max_features`, hiperparámetros, `umbral`, `seed` | | Cada uno su parte |

El modelo guardado queda así:

```python
Pipeline([
    ("preprocesamiento", TextPreprocessor(modo="lema")),   # fases 1–4
    ("tfidf", crear_vectorizador(config)),                  # fase 5
    ("modelo", LogisticRegression(...)),                    # fase 6
])
```

> **Regla de oro:** el backend carga `modelo.joblib` (que ya trae las fases 1 a 6) y **nunca reimplementa el preprocesamiento**.
> Tener todo en `config.yaml` hace que las modificaciones en vivo sean cambiar una línea y reentrenar.

### 3.4 Contrato de la API (FastAPI)

FastAPI se justifica porque valida las entradas con Pydantic y genera la documentación de los endpoints sola (`/docs`).

| Método | Endpoint | Entrada | Salida |
|---|---|---|---|
| GET | `/health` | — | `{estado, modelo_cargado, tienda_cargada}` |
| POST | `/predict` | `{texto}` | `{intencion, probabilidad, top3}` |
| POST | `/predict/lote` | archivo `.csv`/`.txt` con varios textos | lista de predicciones |
| POST | `/chat` | `{texto, rol}` | `{intencion, probabilidad, entidades, respuesta, pasos}` |
| GET | `/metrics` | — | métricas de los dos modelos + matriz de confusión |
| POST | `/tienda/importar` | archivos de la tienda | resumen de lo importado |
| GET | `/reportes/{tipo}` | rango de fechas | datos para el panel admin |

Errores: texto vacío → 422, texto de más de 500 caracteres → 422, archivo con formato incorrecto → 400, siempre con un mensaje claro en español.

---

## 4. Cronograma

| Día | Carmen | Fernando | Ramiro | Jorge | Hito del día |
|---|---|---|---|---|---|
| **Jue 29 oct** | Fase 1: `normalizar` · primeras frases del dataset | Fase 3: lista de stop words y su justificación | Fase 5: primer `TfidfVectorizer` sobre texto sin limpiar | Fase 6: esqueleto de `train.py`, línea base, `requirements.txt` | Contratos de la sección 3 acordados · tema aprobado por el docente · todos aportan frases |
| **Vie 30 oct** | Fase 2: `tokenizar` · dataset completo (≥ 1.000) · EDA | Fase 4: `lematizar` (spaCy) y `stemmizar` (Snowball) · `TextPreprocessor` | Fase 5: unigramas vs uni+bigramas, parámetros · esqueleto FastAPI con `/health` | Fase 6: regresión logística vs Naive Bayes con el pipeline completo | **Primer `modelo.joblib` con las 6 fases, generado con un comando** |
| **Sáb 31 oct** | División estratificada y desbalance · importador + tienda demo | Comparación stem vs lema · frontend: esqueleto (React + Vite) y chat de texto | `/predict`, `/chat`, `/metrics` · `extraer_entidades` | `GridSearchCV` · análisis de errores · `metricas.json` | API respondiendo con el modelo real |
| **Dom 1 nov** | Frontend: panel admin con reportes y subida de archivo | Frontend: voz (Web Speech API) y vista del preprocesamiento | `/reportes`, `/predict/lote`, pruebas `pytest` · opcional: embeddings | Matriz de confusión y F1 por clase · panel de métricas · README de entrenamiento | Sistema completo funcionando de punta a punta |
| **Lun 2 nov** | Informe: datos y fases 1–2 | Informe: fases 3–4 y frontend | Informe: fase 5 y API · `CONTRIBUCIONES.md` | Informe: fase 6 · README final | 18:00 congelamiento · ensayo clonando desde cero · 23:00 tag `entrega-final` |
| **Mar 3 nov** | | | | | **Presentación** |

Si algo se atrasa, se recorta en este orden: embeddings → subida de archivo con varios textos → voz. Lo obligatorio del PDF nunca se recorta.

---

## 5. Tareas por integrante

### Carmen — Fases 1 y 2 + datos
- [ ] `feat/nlp-normalizacion`: `normalizar` con ejemplos antes/después y justificación
- [ ] `feat/nlp-tokenizacion`: `tokenizar` con los casos difíciles del dominio
- [ ] `feat/dataset-intenciones`: `data/raw/intenciones.csv` + origen, licencia y fecha en `data/README.md`
- [ ] `feat/eda`: `notebooks/01_eda.ipynb` — distribución de clases, longitud de textos, palabras más frecuentes, valores faltantes
- [ ] `feat/split`: `src/data/dataset.py` — división estratificada con `seed=42`; justificar el tratamiento del desbalance (`class_weight` o más frases)
- [ ] `feat/tienda-demo` y `feat/importador`: tienda de ejemplo + `importar_tienda` con validación de columnas
- [ ] `feat/frontend-admin`: panel de reportes y subida de archivo

### Fernando — Fases 3 y 4 + frontend
- [ ] `feat/nlp-stopwords`: lista en español + palabras quitadas/agregadas con justificación
- [ ] `feat/nlp-lematizacion`: `lematizar` (spaCy `es_core_news_sm`) y `stemmizar` (NLTK Snowball)
- [ ] `feat/nlp-pipeline`: `TextPreprocessor` + `preprocesar_pasos` (une las fases 1–4)
- [ ] `feat/nlp-comparacion-lema-stem`: métricas con lema vs con stem → elegir uno
- [ ] `feat/frontend-chat`: chat de texto con intención y probabilidad
- [ ] `feat/frontend-voz`: micrófono (`SpeechRecognition`) y respuesta hablada (`SpeechSynthesis`)
- [ ] `feat/frontend-preprocesamiento`: vista paso a paso (normalizado → tokens → stop words eliminadas → lemas)

### Ramiro — Fase 5 + backend
- [ ] `feat/nlp-tfidf`: `crear_vectorizador` con parámetros documentados
- [ ] `feat/nlp-ngramas`: comparar (1,1) vs (1,2) y elegir
- [ ] `feat/nlp-embeddings` (opcional): TF-IDF vs embeddings (vectores de spaCy promediados)
- [ ] `feat/api-base`: FastAPI, `/health`, manejo de errores
- [ ] `feat/entidades`: `extraer_entidades` — talla, color, categoría y producto contra el catálogo; fechas ("hoy", "esta semana", "octubre")
- [ ] `feat/api-chat`: `/predict`, `/chat` (umbral de confianza → "no entendí"), plantillas de respuesta
- [ ] `feat/api-reportes`: `/reportes/{tipo}`, `/tienda/importar`, `/metrics`, `/predict/lote`
- [ ] `feat/tests`: `tests/` con `pytest` (salud, predicción, validaciones, entidades)

### Jorge — Fase 6 + pipeline reproducible
- [ ] `feat/requirements`: dependencias con versiones fijadas (`pip freeze`)
- [ ] `feat/train-baseline`: `train.py` de un solo comando + línea base de clase más frecuente
- [ ] `feat/modelos`: regresión logística vs Naive Bayes; accuracy, F1 macro, F1 por clase
- [ ] `feat/gridsearch`: validación cruzada (`C` para regresión logística, `alpha` para Naive Bayes)
- [ ] `feat/analisis-errores`: `notebooks/03_modelos.ipynb` — frases mal clasificadas y por qué
- [ ] `feat/artefactos`: `modelo.joblib` + `metricas.json` (incluye matriz de confusión)
- [ ] `feat/predict`: `src/models/predict.py`

### Todos
- [ ] Hoy: configurar `git config user.name` y `user.email` con la cuenta propia
- [ ] Hoy: agregar al docente como colaborador del repositorio
- [ ] Hoy: aportar frases al dataset
- [ ] Lunes: su sección en `docs/informe_tecnico.md` y en las diapositivas
- [ ] Lunes: ensayar levantar el sistema desde cero

---

## 6. Reglas de Git del equipo

- `main` protegida: nadie sube directo, todo entra por pull request.
- Una rama por tarea con el nombre de la sección 5 (`feat/...`, `fix/...`, `docs/...`).
- Cada PR lo revisa y aprueba otra persona, siguiendo la cadena de fases (cada uno revisa a quien le entrega su salida):

| Autor del PR | Revisa | Por qué |
|---|---|---|
| Carmen (fases 1–2) | Fernando | Fernando usa los tokens de Carmen |
| Fernando (fases 3–4) | Ramiro | Ramiro vectoriza el texto de Fernando |
| Ramiro (fase 5) | Jorge | Jorge entrena con el vectorizador de Ramiro |
| Jorge (fase 6) | Carmen | Cierra la rotación |

- Mensajes con Conventional Commits, diciendo qué y por qué:
  `feat(nlp): conservar "no" en stop words porque cambia el sentido de la consulta`
- Commits pequeños y **todos los días**; nada de un commit gigante el lunes.
- Trabajo en pareja → línea `Co-authored-by: Nombre <correo>` en el commit.
- Prohibido `git push --force` y squash en `main`.
- Archivos pesados o generados (`artifacts/*.joblib`, `.db`) en `.gitignore`; se regeneran con `python -m src.models.train`.
- El uso de asistentes de IA se declara en el informe; cada uno debe poder explicar y modificar todo lo que subió.

---

## 7. Preparación de la defensa

Cada uno ensaya **antes del martes** al menos una modificación en vivo de su fase:

| Integrante | Modificación a ensayar |
|---|---|
| Carmen (fases 1–2) | Cambiar una regla de normalización (por ejemplo, conservar números o emojis), reentrenar y comparar; agregar frases a una intención |
| Fernando (fases 3–4) | Agregar o quitar una stop word; cambiar lema por stem y comparar métricas |
| Ramiro (fase 5) | Cambiar `ngram_range` o `min_df` y reentrenar; agregar la validación "rechazar textos de menos de 3 palabras" |
| Jorge (fase 6) | Cambiar `C` o `alpha`, reentrenar y comparar; interpretar la matriz de confusión y el F1 por clase |

Además, todos deben poder explicar:
- las 6 fases, no solo la suya (el docente puede preguntar cualquier parte);
- cómo funcionan por dentro la regresión logística y Naive Bayes;
- el recorrido completo de una consulta, desde el micrófono hasta la respuesta hablada.

---

## 8. Preguntas abiertas

- [ ] **Aprobación del docente:** es un tema propio fuera de la tabla del PDF. Pedirla hoy como "clasificación de intenciones de clientes y administradores de tiendas de ropa con TF-IDF + regresión logística / Naive Bayes".
- [ ] El PDF dejó sin completar el tamaño mínimo del dataset y la fecha límite para aprobar temas: confirmar con el docente.
- [ ] Framework del frontend: se propone React + Vite. ¿Alguien prefiere otro?
- [ ] Embeddings: ¿entran como comparación extra contra TF-IDF o se dejan fuera por tiempo?
- [ ] Duración de la exposición el día de la presentación.
