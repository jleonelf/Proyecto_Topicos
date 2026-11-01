# Asistente Virtual para Tiendas de Ropa

Proyecto integrador de Procesamiento de Lenguaje Natural (NLP) y Machine Learning (ML) con API REST y frontend web para clasificación de intenciones de clientes y administradores, con detector y calibración de rechazo fuera de dominio (OOD).

---

## 1. Estructura del Repositorio

```text
Proyecto_Topicos/
├── .github/workflows/       # Verificaciones continuas de CI
├── api/                     # Backend y rutas de FastAPI
│   └── routes/              # Endpoints REST (/predict, /chat, /metrics)
├── artifacts/               # Modelos, detectores y métricas generadas
│   ├── modelo.joblib        # Pipeline completo serializado (Fases 1 a 6)
│   ├── ood_detector.joblib  # Detector de rechazo OOD serializado (Dual-Gate)
│   └── metricas.json        # Métricas de CV, evaluación final y benchmark OOD
├── data/                    # Datos crudos, procesados y conjuntos OOD
│   ├── raw/                 # intenciones.csv (1.040 registros balanceados, 13 clases)
│   ├── ood_val.csv          # 40 consultas OOD de validación para calibración
│   ├── ood_test.csv         # 50 consultas OOD de prueba (incluye bug reports)
│   ├── README.md            # Documentación del dataset en dominio
│   └── OOD_README.md        # Especificación y taxonomía de datasets OOD
├── docs/                    # Plan de trabajo y especificaciones académicas
├── frontend/                # Interfaz de usuario (chat y panel admin)
├── notebooks/               # Notebooks reproducibles de experimentación
│   └── 03_modelos.ipynb     # Modelado ML, matrices, OOD benchmark y análisis de errores
├── src/                     # Código fuente modular
│   ├── config.yaml          # Parámetros centrales del pipeline y umbrales OOD
│   ├── data/                # Carga y división estratificada de datos
│   ├── nlp/                 # Pipeline NLP (normalización, tokens, stopwords, lemas, TF-IDF)
│   └── models/              # Modelado ML y detección OOD
│       ├── train.py         # Entrenamiento con CV 5-folds y persistencia
│       ├── predict.py       # Inferencia con contrato estricto y filtro OOD
│       └── ood.py           # Detectores modulares OOD (MSP, Margin, Cosine, Cov, Hybrid)
├── tests/                   # Pruebas automatizadas con pytest
│   ├── test_models.py       # Pruebas unitarias y de integración de modelos e inferencia
│   └── test_ood.py          # Pruebas de detección OOD, rechazo de bugs y calibración
├── requirements.txt         # Dependencias con versiones fijadas
└── pytest.ini               # Configuración de pruebas
```

---

## 2. Instalación y Preparación del Entorno

### Requisitos previos
- Python 3.11 o superior instalado.
- Gestor de paquetes `pip` y Git.

### Paso 1: Clonar el repositorio y crear entorno virtual

```bash
git clone <url-del-repositorio>
cd Proyecto_Topicos

# Crear entorno virtual
python -m venv .venv

# Activar en Windows (PowerShell)
.\.venv\Scripts\Activate.ps1

# Activar en Linux / macOS
source .venv/bin/activate
```

### Paso 2: Instalar dependencias con versiones fijadas

```bash
pip install -r requirements.txt
```

### Paso 3: Descargar el modelo de lenguaje de spaCy en español

El pipeline de NLP requiere el modelo lematizador en español `es_core_news_sm` cuando `nlp.modo` está configurado en `lema` (por defecto en `src/config.yaml`):

```bash
python -m spacy download es_core_news_sm
```

> **Nota de robustez:** Si el modelo de spaCy no está presente, el sistema no recurre silenciosamente a tokens sin procesar; emitirá un error `RuntimeError` explícito solicitando la descarga del modelo.

---

## 3. Arquitectura de Machine Learning y Metodología Rigurosa

El sistema implementa una arquitectura desacoplada de dos etapas para la toma de decisiones:

```
[ Consulta de Usuario ]
          │
          ▼
┌────────────────────────────────────────────────────────┐
│  Fases 1 a 5: Pipeline NLP Completo                    │
│  - Limpieza, normalización y remoción de puntuación    │
│  - Tokenización y filtrado de Stopwords customizadas   │
│  - Lematización morfológica con spaCy (es_core_news_sm)│
│  - Vectorización TF-IDF (1-2 gramas, max_features=2000)│
└────────────────────────────────────────────────────────┘
          │
          ├───────────────────────────────┐
          ▼                               ▼
┌──────────────────────────┐    ┌──────────────────────────────────┐
│  Fase 6A: Clasificador   │    │  Fase 6B: Detector OOD           │
│  Regresión Logística     │    │  Hybrid Dual-Gate                │
│  Multinomial             │    │  - Softmax MSP >= 0.35           │
│  (Probabilidades softmax)│    │  - Cobertura Vocabulario >= 0.40 │
└──────────────────────────┘    └──────────────────────────────────┘
          │                               │
          ▼                               ▼
    [ Clase más probable ]        [ ¿Supera filtros OOD? ]
          │                               │
          └───────────────┬───────────────┘
                          │
             ┌────────────┴────────────┐
             │ ¿Confianza suficiente?  │
             └────────────┬────────────┘
                   Sí ───┴─── No
                   │          │
                   ▼          ▼
             [ Intención ]  [ "no_entendido" ]
```

### Principios metodológicos (Sin Data Leakage):
1. **División estratificada fija (`seed=42`):** 80% entrenamiento (`X_train`: 832 ejemplos) y 20% prueba independiente (`X_test`: 208 ejemplos).
2. **Selección del clasificador exclusivamente por Validación Cruzada:**
   - Se optimiza `GridSearchCV` con 5 particiones estratificadas (`StratifiedKFold`) sobre `X_train`.
   - El modelo ganador para producción se selecciona **exclusivamente por mayor F1 Macro en CV**. El conjunto `X_test` **nunca se utiliza para decidir modelos o hiperparámetros**.
3. **Evaluación final única en prueba independiente:** Se evalúa el modelo ganador una sola vez sobre `X_test` para reportar métricas de generalización no sesgadas.
4. **Calibración OOD en validación abierta (Open-Set):**
   - El umbral de rechazo OOD **no se asume arbitrariamente ni se calibra sobre datos cerrados en dominio**.
   - Se evalúa cuantitativamente contra `data/ood_val.csv` (40 consultas de 10 dominios externos).
   - Se selecciona la estrategia con mayor F1 macro con rechazo entre las que aceptan como máximo el 20% de consultas OOD de validación. El conjunto OOD de prueba se evalúa solo después de esta selección.

---

## 4. Tabla de Métricas Reales

Los siguientes valores corresponden fielmente a los reportados en `artifacts/metricas.json`:

### Comparativa de Modelos Candidatos (Fase 6A)

| Modelo | Hiperparámetros Óptimos | CV F1 Macro (Train) | Test Accuracy | Test F1 Macro | Test F1 Weighted |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **Línea Base (Dummy)** | `strategy='most_frequent'` | 0.0000 | 0.0769 (7.69%) | 0.0110 | 0.0110 |
| **Naive Bayes (ComplementNB)** | `alpha=2.0` | 0.8009 | 0.8365 (83.65%) | 0.8375 | 0.8375 |
| **Regresión Logística (Ganador)** | `C=10.0`, `class_weight='balanced'` | **0.8489** | **0.8606 (86.06%)** | **0.8622** | **0.8622** |

*Criterio de selección para producción:* Mayor F1 Macro en validación cruzada estratificada de 5 folds sobre `X_train` (**Regresión Logística: 0.8489** vs Naive Bayes: 0.8009).

### Comparativa de Estrategias de Rechazo OOD (Fase 6B)

Evaluación en conjunto de validación abierta (`data/ood_val.csv`, 40 consultas externas):

| Estrategia | Parámetros | Cobertura ID | Exactitud Aceptadas | Tasa Error OOD (FPR) | F1 Macro con Rechazo | Score Balance |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **MSP Baseline (0.35)** | `umbral=0.35` | 85.0% | 90.1% | 35.0% | 0.8202 | 0.7979 |
| **MSP Calibrado** | `umbral=0.675` | 47.9% | 95.0% | 15.0% | 0.5868 | 0.7434 |
| **Margen entre Clases** | `umbral=0.60` | 46.1% | 96.1% | 15.0% | 0.5702 | 0.7379 |
| **Similitud Coseno Centroides** | `umbral=0.25` | 38.3% | 90.6% | 12.5% | 0.4540 | 0.6723 |
| **Cobertura de Vocabulario** | `umbral=0.60` | 91.6% | 84.3% | 10.0% | 0.8048 | 0.8382 |
| **Hybrid Dual-Gate (Ganador)** | `prob>=0.35, cov>=0.40` | **83.2%** | **90.7%** | **20.0%** | **0.8151** | **0.8342** |

La selección usa **F1 macro con rechazo**, sujeto a una tasa de aceptación OOD de validación de hasta 20%. `Score Balance` se informa como dato adicional; por ese indicador aislado gana cobertura de vocabulario.

### Evaluación final independiente del detector seleccionado

Tras fijar la estrategia y sus umbrales se midieron 208 consultas ID y 50 OOD de prueba, sin usarlas para seleccionar el detector. El híbrido aceptó el **87,5%** de las ID; su exactitud entre las aceptadas fue **90,11%** y su F1 macro con rechazo **0,8402**. Aceptó por error **8/50 OOD (16%)**: **0/25 fáciles** y **8/25 difíciles (32%)**. Estos resultados describen el alcance de los dos conjuntos de prueba; el detector no garantiza rechazo de toda consulta ajena a la tienda.

---

## 5. Resolución del Bug Report (Casos Adversarios OOD)

### Análisis del problema original:
Bajo un clasificador tradicional que solo usa umbral de probabilidad (MSP):
1. *"cómo cambiar la contraseña del wifi"* $\rightarrow$ Activa el verbo *"cambiar"* y predice `devoluciones` con confianza **0.8112** (Falso Positivo).
2. *"tengo fiebre y dolor de cabeza"* $\rightarrow$ Activa el verbo *"tengo"* y predice `consultar_tallas` con confianza **0.6390** (Falso Positivo).
3. *"¿cuánto cuesta un pasaje de avión?"* $\rightarrow$ Activa la fórmula *"cuánto cuesta"* y predice `consultar_precio` con confianza **0.6825** (Falso Positivo).

### Solución implementada (Dual-Gate):
El detector `HybridOODDetector` analiza la **cobertura léxica lematizada** de la frase contra el vocabulario específico de la tienda de ropa. Dado que los términos *contraseña, wifi, fiebre, dolor, cabeza, pasaje, avión* no pertenecen al dominio, la cobertura de estas tres frases es de solo **0.25 (25%)**, quedando por debajo del umbral de cobertura calibrado (**0.40**).

Resultado:
- **Las 3 consultas son rechazadas** devolviendo `intencion: "no_entendido"` con `confianza_suficiente: false`. El método `diagnosticar` del detector informa `cobertura_baja` como motivo.
- **Sin listas negras ad-hoc:** No se añadieron palabras prohibidas ni reglas *if-else* rígidas; el detector opera con base en propiedades estadísticas del vocabulario del dominio.

---

## 6. Pruebas Automatizadas

La suite de pruebas cubre entrenamiento, inferencia y rechazo OOD:

```bash
# Ejecutar toda la suite con reporte detallado
python -m pytest -v
```

### Pruebas en `tests/test_models.py`:
- `test_cargar_configuracion`: Valida existencia y claves obligatorias de `src/config.yaml`.
- `test_entrenar_y_generar_artefactos`: Valida la ejecución reproducible de entrenamiento, persistencia de `modelo.joblib`, `metricas.json` y criterio de selección por CV.
- `test_predecir_contrato_estricto`: Valida el contrato estricto de retorno (`texto`, `intencion`, `intencion_detectada`, `probabilidad`, `top3`, `umbral`, `confianza_suficiente`).
- `test_predecir_consultas_en_dominio_validas`: Comprueba que consultas legítimas de clientes y administradores superen el filtro y no devuelvan `no_entendido`.
- `test_predecir_consultas_ood_no_vistas_rechazadas`: Verifica el rechazo de ejemplos concretos del conjunto OOD de prueba; las métricas finales informan también los casos aceptados por error.
- `test_predecir_texto_vacio_y_espacios`: Manejo seguro de cadenas vacías o espacios en blanco sin excepciones.
- `test_predecir_top3_ordenado`: Garantiza que el Top 3 esté ordenado descendentemente por probabilidad.
- `test_rutas_relativas_y_absolutas`: Valida que `cargar_modelo()` y `predecir()` resuelvan rutas relativas, absolutas o cuando se ejecutan desde cualquier directorio de trabajo (`cwd`).
- `test_regeneracion_desde_cero`: Valida que `invalidar_cache()` limpie la memoria y permita recargar o reentrenar modelos sin depender de artefactos antiguos en caché.
- `test_lematizacion_error_si_falta_spacy`: Confirma que la ausencia de `es_core_news_sm` genera un error explícito `RuntimeError`.
- `test_detector_faltante_o_roto_no_acepta_consultas`: Verifica que inferencia genere un error claro si falta el detector o falla su ejecución.

### Pruebas en `tests/test_ood.py`:
- `test_instanciacion_y_score_detectores`: Valida ajuste y cálculo de scores continuos en los detectores MSP, Margen, Cobertura e Híbrido.
- `test_estrategia_hibrida_rechaza_bugs_reportados`: Comprueba explícitamente el rechazo de las 3 consultas del bug report (*wifi*, *fiebre*, *pasaje de avión*).
- `test_estrategia_hibrida_acepta_consultas_en_dominio`: Verifica que consultas legítimas en dominio mantengan una alta cobertura y sean aceptadas.
- `test_evaluacion_y_comparacion_estrategias`: Valida la ejecución de la grilla comparativa `comparar_estrategias()`.
- La misma prueba verifica que la estrategia seleccionada siga el criterio cuantitativo declarado.
- `test_sin_listas_negras_ni_reglas_ad_hoc`: Inspecciona el código de `src/models/ood.py` para garantizar la ausencia de listas negras o palabras clave codificadas a mano.

---

## 7. Inferencia y Uso del Sistema

El comando de entrenamiento genera `modelo.joblib` y `ood_detector.joblib`. Si falta el detector o falla su evaluación, inferencia genera un error explícito; no vuelve al umbral MSP que aceptaba las consultas del bug report.

### Ejecución por terminal

```bash
# Consulta en dominio
python -m src.models.predict "¿tienen pantalones jeans en talla 32?"
```

Salida en formato YAML:
```yaml
texto: "¿tienen pantalones jeans en talla 32?"
intencion: "consultar_tallas"
intencion_detectada: "consultar_tallas"
probabilidad: 0.8585
umbral: 0.35
confianza_suficiente: true
top3:
  - intencion: "consultar_tallas"
    probabilidad: 0.8585
  - intencion: "consultar_stock"
    probabilidad: 0.0812
  - intencion: "consultar_precio"
    probabilidad: 0.0234
```

```bash
# Consulta fuera de dominio (OOD)
python -m src.models.predict "cómo cambiar la contraseña del wifi"
```

Salida en formato YAML:
```yaml
texto: "cómo cambiar la contraseña del wifi"
intencion: "no_entendido"
intencion_detectada: "devoluciones"
probabilidad: 0.8112
umbral: 0.35
confianza_suficiente: false
top3:
  - intencion: "devoluciones"
    probabilidad: 0.8112
  - intencion: "envios"
    probabilidad: 0.0302
  - intencion: "consultar_stock"
    probabilidad: 0.0186
```

### Uso programático en Python

```python
from src.models.predict import predecir

resultado = predecir("¿cuánto cuesta el vestido de fiesta?")
print(resultado["intencion"])            # 'consultar_precio'
print(resultado["probabilidad"])           # 0.3948
print(resultado["confianza_suficiente"])   # True
```

---

## 8. Límites Reales del Sistema y Honestidad Intelectual

De acuerdo con las buenas prácticas de ingeniería de Machine Learning, documentamos las limitaciones observadas:

1. **Ambigüedad de Rol (Cliente vs Administrador):**
   Consultas como *"¿qué ropa tiene pocas unidades disponibles?"* comparten vocabulario idéntico con consultas de stock de clientes (*"¿tienen unidades disponibles?"*). Al tratarse de un modelo de procesamiento lingüístico puro sin información de sesión o autenticación, el clasificador puede inclinarse hacia `consultar_stock` en lugar de `stock_bajo`. Se recomienda que la capa de API verifique el rol del usuario (JWT / token) antes de enrutar la intención.
2. **Consultas OOD con Alto Solapamiento Textil:**
   Si una consulta ajena al negocio incluye múltiples palabras del dominio de ropa (por ejemplo: *"¿dónde puedo aprender a coser un vestido de novia?"* o *"quiero confeccionar camisas de seda"*), la cobertura de vocabulario en TF-IDF puede superar el umbral calibrado y ser aceptada erróneamente. La mitigación futura para este escenario involucra modelos neuronales densos (embeddings con bi-encoders y Sentence Transformers).
3. **Fórmulas de Cortesía Combinadas:**
   Frases cordiales que combinan fórmulas de saludo y despedida (*"buenas noches y muchas gracias hasta luego"*) activan n-gramas de ambas clases, generando competencia entre `saludo` y `despedida`.
4. **Dependencia del Preprocesador Morfológico:**
   El pipeline depende de la calidad morfológica del modelo `es_core_news_sm` de spaCy. Errores tipográficos severos o modismos regionales no contemplados en el diccionario lematizador pueden reducir la cobertura calculada.

---

## 9. Ejecución del Notebook de Modelado

El notebook `notebooks/03_modelos.ipynb` contiene todo el flujo reproducible ejecutado de inicio a fin:
- Inspección de configuración.
- Entrenamiento con CV estratificada de 5 folds.
- Tablas comparativas y gráficos de F1 por clase.
- Matriz de confusión interactiva.
- Análisis cualitativo de errores reales.
- Benchmark OOD y diagnóstico del bug report.
- Batería de pruebas de inferencia.

Para reejecutarlo y regenerar todas las celdas en sitio:

```bash
python -m nbconvert --to notebook --execute --inplace notebooks/03_modelos.ipynb
```
