# Documentación del Conjunto de Datos

## `data/raw/intenciones.csv`

Dataset para entrenamiento del clasificador de intenciones del Asistente Virtual para tiendas de ropa.

* **Origen:** Recolectado manualmente por el equipo de desarrollo (frases sintéticas y consultas frecuentes de comercio electrónico).
* **Idioma:** Español.
* **Licencia:** MIT / Uso académico.
* **Fecha de obtención:** 29 de octubre de 2026.
* **Estructura de columnas:**
  * `texto`: Frase o consulta en lenguaje natural emitida por el usuario.
  * `intencion`: Etiqueta de la intención (13 clases: `saludo`, `despedida`, `consultar_stock`, `consultar_precio`, `consultar_tallas`, `envios`, `devoluciones`, `horarios_ubicacion`, `metodos_pago`, `reporte_ventas`, `productos_mas_vendidos`, `stock_bajo`, `ventas_por_categoria`).
  * `rol`: Rol del usuario (`cliente` o `admin`).
  * `fuente`: Origen del dato (`manual`, `parafraseo`, `ia`).
