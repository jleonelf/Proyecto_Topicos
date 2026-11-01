# Documentación del Conjunto de Datos

## `data/raw/intenciones.csv`

Dataset para entrenamiento y evaluación del clasificador de intenciones del Asistente Virtual para tiendas de ropa.

* **Origen:** Recolectado inicialmente de forma manual por el equipo de desarrollo (138 frases) y posteriormente ampliado de forma responsable con asistencia de IA (902 frases) para alcanzar la meta establecida de 80 frases por intención (1.040 frases en total), cubriendo variedad de prendas, tallas, expresiones formales e informales, y consultas administrativas.
* **Idioma:** Español.
* **Licencia:** MIT / Uso académico.
* **Fecha de actualización:** 31 de octubre de 2026.
* **Estructura de columnas:**
  * `texto`: Frase o consulta en lenguaje natural emitida por el usuario.
  * `intencion`: Etiqueta de la intención (13 clases: `saludo`, `despedida`, `consultar_stock`, `consultar_precio`, `consultar_tallas`, `envios`, `devoluciones`, `horarios_ubicacion`, `metodos_pago`, `reporte_ventas`, `productos_mas_vendidos`, `stock_bajo`, `ventas_por_categoria`).
  * `rol`: Rol del usuario (`cliente` o `admin`).
  * `fuente`: Origen del dato (`manual`, `ia`).

### Distribución del Dataset

* **Total de registros:** 1.040
* **Por intención (balanceado a 80 registros por clase):**
  1. `saludo`: 80 (12 manual, 68 ia)
  2. `despedida`: 80 (11 manual, 69 ia)
  3. `consultar_stock`: 80 (12 manual, 68 ia)
  4. `consultar_precio`: 80 (11 manual, 69 ia)
  5. `consultar_tallas`: 80 (11 manual, 69 ia)
  6. `envios`: 80 (11 manual, 69 ia)
  7. `devoluciones`: 80 (10 manual, 70 ia)
  8. `horarios_ubicacion`: 80 (10 manual, 70 ia)
  9. `metodos_pago`: 80 (10 manual, 70 ia)
  10. `reporte_ventas`: 80 (10 manual, 70 ia)
  11. `productos_mas_vendidos`: 80 (10 manual, 70 ia)
  12. `stock_bajo`: 80 (10 manual, 70 ia)
  13. `ventas_por_categoria`: 80 (10 manual, 70 ia)
* **Por rol:**
  * `cliente`: 720 registros (9 intenciones × 80)
  * `admin`: 320 registros (4 intenciones × 80)
* **Por fuente:**
  * `manual`: 138 registros
  * `ia`: 902 registros
