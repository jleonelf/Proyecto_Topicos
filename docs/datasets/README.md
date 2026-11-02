# Datasets del proyecto

Tres datasets construidos a partir de fuentes públicas, con origen, licencia y fecha de obtención documentados (requisito del enunciado, sección 4). Se regeneran con un solo comando desde la raíz del proyecto:

```bash
python docs/datasets/construir_datasets.py
```

El script lee las fuentes por streaming en memoria (las de Amazon pesan cientos de MB) y solo guarda los Excel. Cada Excel incluye una hoja `fuentes` con todo el detalle.

| # | Archivo | Filas | Idioma | Uso en el proyecto |
|---|---|---|---|---|
| 1 | `dataset_1_intenciones_atencion_cliente.xlsx` | 6.320 frases | Español | Entrenar el clasificador de intenciones |
| 2 | `dataset_2_consultas_fuera_de_dominio.xlsx` | 25.538 consultas | Español | Calibrar y evaluar el detector de rechazo (OOD) |
| 3 | `dataset_3_inventario_ventas_amazon.xlsx` | 8.000 productos + 15.000 ventas | Español (nombres derivados; título original en inglés) | Importar en "Inventarios y métricas"; respuestas del chatbot |

Fecha de obtención: 2 de noviembre de 2026.

## 1. Intenciones de atención al cliente

- **Fuente:** Bitext, *Customer Service Tagged Training Dataset for LLM-based Virtual Assistants*, traducción al español publicada en Hugging Face: [Faramir/Bitext-customer-support-llm-chatbot-training-dataset-spanish](https://huggingface.co/datasets/Faramir/Bitext-customer-support-llm-chatbot-training-dataset-spanish). Original en inglés: [bitext/Bitext-customer-support-llm-chatbot-training-dataset](https://huggingface.co/datasets/bitext/Bitext-customer-support-llm-chatbot-training-dataset).
- **Licencia:** CDLA-Sharing-1.0 (permite usar, modificar y compartir citando la fuente).
- **Columnas:** `texto, intencion, rol, fuente` (formato de `intenciones.csv` del plan) + `intencion_original, categoria_original`.
- **Contenido:** 10 intenciones de Bitext mapeadas a 3 del proyecto (hoja `mapeo`):

| Intención del proyecto | Frases | Intenciones de Bitext |
|---|---|---|
| `envios` | 2.947 | delivery_options, delivery_period, track_order, change_shipping_address, set_up_shipping_address |
| `devoluciones` | 1.745 | check_refund_policy, get_refund, track_refund |
| `metodos_pago` | 1.628 | check_payment_methods, payment_issue |

- **Limitaciones:**
  - Cubre 3 de las 13 intenciones. `saludo`, `despedida`, `consultar_stock`, `consultar_precio`, `consultar_tallas`, `horarios_ubicacion` y las 4 de administración no tienen una fuente pública en español: las aporta el dataset del grupo (`fuente = manual` o `real`).
  - La traducción es automática y algunas frases suenan poco naturales.
  - Para no desbalancear las clases al combinarlo con el dataset del grupo, conviene tomar una muestra estratificada por intención.

## 2. Consultas fuera de dominio

- **Fuente 1:** MASSIVE es-ES de Amazon Science ([copia en Hugging Face](https://huggingface.co/datasets/SetFit/amazon_massive_intent_es-ES), [original](https://huggingface.co/datasets/AmazonScience/massive)). FitzGerald et al. (2022), arXiv:2204.08582. **Licencia CC BY 4.0.** 15.872 consultas a un asistente de voz (alarmas, clima, música...), `dificultad = facil`. Se excluyó `general_greet` porque los saludos sí son del dominio.
- **Fuente 2:** las 17 intenciones de Bitext que no responde una tienda de ropa (cuentas, facturas, contraseñas, boletín, quejas, pedidos). **Licencia CDLA-Sharing-1.0.** 9.666 consultas, `dificultad = dificil`: parecen atención al cliente pero el chatbot debe rechazarlas.
- **Columnas:** `texto, categoria, dificultad, fuente` (formato de `ood_val.csv` de Jorge) + `intencion_original`.

## 3. Inventario y ventas

- **Fuente:** Amazon Reviews'23, categoría Amazon_Fashion ([web](https://amazon-reviews-2023.github.io/)), McAuley Lab, UC San Diego. Cita: Hou, Y., Li, J., He, Z., Yan, A., Chen, X., & McAuley, J. (2024). *Bridging Language and Items for Retrieval and Recommendation*. arXiv:2403.03952.
- **Licencia:** la página no declara una licencia explícita (© 2024 McAuley Lab); se publica para investigación y se usa con fines académicos citando el artículo.
- **Hojas:** `productos` y `ventas` en el formato de importación del plan (sección 3.2), listas para subir en "Inventarios y métricas".

| Columna | Origen |
|---|---|
| `sku` | Real: `parent_asin` de Amazon |
| `nombre` | Derivado: tipo de prenda + público (mujer/hombre/infantil) + marca + color, en español |
| `nombre_original` | Real: título publicado en Amazon (inglés) |
| `categoria` | Derivado: traducida desde palabras del título (dress → vestidos...) |
| `color` | Real: primer color mencionado en el título, traducido (3.073 productos lo tienen) |
| `talla` | Real cuando el título la trae; vacía en la mayoría (Amazon agrupa todas las tallas en un mismo producto) |
| `precio`, `precio_unitario` | Derivado: precio en USD × 6,96 Bs (tipo de cambio oficial del BCB) |
| `precio_usd`, `marca`, `valoracion_promedio`, `num_valoraciones` | Reales |
| `stock` | **Simulado** (Amazon no publica inventario): valor reproducible de 0 a 40; columna `stock_origen = simulado` |
| ventas: `fecha`, `calificacion` | Reales: cada reseña con compra verificada (`verified_purchase`) cuenta como una venta de 1 unidad, del 25/11/2022 al 10/09/2023 |

- **Selección:** productos con precio y con categoría de ropa reconocible (35.481 de 826.108). Se limitó joyería, accesorios y calcetines a 400 cada uno, porque Amazon Fashion vende sobre todo eso, y se priorizaron los más vendidos.
- **Limitaciones:**
  - La categoría por palabras clave falla en algunos casos (un calzador quedó como calzado).
  - El precio de las ventas es el de catálogo, no el que se pagó ese día.
  - Las ventas son un mínimo, porque no todos los compradores escriben reseña.
