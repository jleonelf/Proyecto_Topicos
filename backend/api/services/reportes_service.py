"""Servicio de lógica de negocio para métricas, reportes administrativos e importaciones.

Responsable: Ramiro (Backend)
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.config import config
from src.data.conexion import consultar
from api.services.chat_service import predecir_intencion

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent.parent

# Tipos de reportes administrativos permitidos
TIPOS_REPORTES_VALIDOS = {
    "ventas": "Reporte general de ventas e ingresos",
    "mas_vendidos": "Ranking de productos con mayor rotación",
    "stock_bajo": "Alerta de artículos con inventario crítico",
    "categorias": "Desglose de rendimiento por categoría de prenda",
}


def obtener_ruta_metricas() -> Path:
    """Ruta al archivo artifacts/metricas.json."""
    rel = config.get("rutas", {}).get("metricas_guardadas", "artifacts/metricas.json")
    return RAIZ_PROYECTO / rel


def obtener_metricas_modelo() -> Dict[str, Any]:
    """Métricas reales del modelo en producción, en el formato plano de MetricsResponse.

    artifacts/metricas.json (lo genera train.py de Jorge) guarda las métricas
    anidadas por modelo; aquí se toman las del modelo en producción y la
    comparación con los demás. Si todavía no hay entrenamiento se devuelven
    ceros, nunca valores inventados. (Adaptación: Fernando)
    """
    from api.services.metricas_service import metricas_entrenamiento

    datos = metricas_entrenamiento()
    if not datos.get("disponible"):
        return {"modelo_activo": "Sin entrenar (ejecutar python -m src.models.train)", "accuracy": 0.0, "f1_macro": 0.0}

    produccion = next((m for m in datos["modelos"] if m["en_produccion"]), datos["modelos"][0])
    return {
        "modelo_activo": datos["produccion"]["nombre"],
        "accuracy": produccion["accuracy"],
        "f1_macro": produccion["f1_macro"],
        "f1_por_clase": {clase: m["f1"] for clase, m in produccion["por_clase"].items()},
        "matriz_confusion": {
            "descripcion": f"Conjunto de prueba ({datos['muestras_test']} frases). Filas: intención real; columnas: predicha.",
            "etiquetas": datos["clases"],
            "valores": produccion["matriz_confusion"],
        },
        "comparativa_modelos": {
            m["nombre"]: {
                "accuracy": m["accuracy"],
                "f1_macro": m["f1_macro"],
                "f1_weighted": m["f1_weighted"],
                "cv_f1_macro": m["cv_f1_macro"],
                "seleccionado": m["en_produccion"],
            }
            for m in datos["modelos"]
        },
    }


def obtener_reporte(tipo: str, rango: Optional[str] = None) -> Dict[str, Any]:
    """Genera datos agregados para el panel de administración.

    Consulta las tablas reales de la base de datos de la tienda (PostgreSQL en Docker,
    SQLite sin Docker). Si no está disponible, provee datos de muestra estructurados
    para alimentar el panel del frontend.
    """
    tipo_limpio = tipo.lower().strip()
    if tipo_limpio not in TIPOS_REPORTES_VALIDOS:
        opciones = ", ".join(f"'{k}'" for k in TIPOS_REPORTES_VALIDOS.keys())
        raise ValueError(
            f"Tipo de reporte '{tipo}' no válido. Opciones permitidas: {opciones}."
        )

    periodo = rango or "Últimos 30 días"

    # Intentar consultar la base de datos real
    try:
        if tipo_limpio == "ventas":
            fila = consultar("SELECT SUM(cantidad * precio_unitario) as total, SUM(cantidad) as items, COUNT(*) as tx FROM ventas")[0]
            total = float(fila["total"] or 0.0)
            items = int(fila["items"] or 0)
            tx = int(fila["tx"] or 0)
            return {
                "tipo_reporte": "ventas",
                "rango": periodo,
                "resumen": {"total_ingresos": total, "transacciones": tx, "articulos_vendidos": items},
                "datos": [{"metrica": "Ticket promedio", "valor": round(total / tx, 2) if tx > 0 else 0}],
            }

        if tipo_limpio == "stock_bajo":
            filas = consultar("SELECT nombre, categoria, talla, color, stock FROM productos WHERE stock <= 5 ORDER BY stock ASC LIMIT 20")
            return {
                "tipo_reporte": "stock_bajo",
                "rango": "Actual",
                "resumen": {"total_alertas": len(filas), "criterio": "Stock <= 5 unidades"},
                "datos": filas,
            }
    except Exception:
        pass

    # Datos demostrativos de respaldo (para desarrollo del panel admin del frontend)
    if tipo_limpio == "ventas":
        return {
            "tipo_reporte": "ventas",
            "rango": periodo,
            "resumen": {
                "total_ingresos": 18450.0,
                "transacciones": 142,
                "articulos_vendidos": 198,
                "moneda": "BOB / Bs",
            },
            "datos": [
                {"fecha": "2026-10-25", "ventas": 2100.0, "pedidos": 18},
                {"fecha": "2026-10-26", "ventas": 2850.0, "pedidos": 22},
                {"fecha": "2026-10-27", "ventas": 3400.0, "pedidos": 26},
                {"fecha": "2026-10-28", "ventas": 3100.0, "pedidos": 24},
                {"fecha": "2026-10-29", "ventas": 3900.0, "pedidos": 29},
                {"fecha": "2026-10-30", "ventas": 3100.0, "pedidos": 23},
            ],
        }

    if tipo_limpio == "mas_vendidos":
        return {
            "tipo_reporte": "mas_vendidos",
            "rango": periodo,
            "resumen": {"total_analizado": "Top 5 productos", "criterio": "Unidades facturadas"},
            "datos": [
                {"posicion": 1, "producto": "Jeans Clásico Denim", "unidades": 58, "ingresos": 6960.0},
                {"posicion": 2, "producto": "Chaqueta Biker Cuero", "unidades": 42, "ingresos": 7980.0},
                {"posicion": 3, "producto": "Polera Básica Algodón", "unidades": 39, "ingresos": 2340.0},
                {"posicion": 4, "producto": "Vestido Casual Floreado", "unidades": 28, "ingresos": 3360.0},
                {"posicion": 5, "producto": "Botines Urbanos", "unidades": 21, "ingresos": 4200.0},
            ],
        }

    if tipo_limpio == "stock_bajo":
        return {
            "tipo_reporte": "stock_bajo",
            "rango": "Inventario en tiempo real",
            "resumen": {"total_alertas": 4, "criterio": "Stock <= 5 unidades"},
            "datos": [
                {"producto": "Jeans Negro Slim", "talla": "32", "color": "negro", "stock": 2, "categoria": "pantalones"},
                {"producto": "Polera Estampada Tokio", "talla": "M", "color": "blanco", "stock": 3, "categoria": "camisetas"},
                {"producto": "Chaqueta Biker Cuero", "talla": "L", "color": "café", "stock": 1, "categoria": "abrigos"},
                {"producto": "Vestido Noche", "talla": "S", "color": "rojo", "stock": 2, "categoria": "vestidos"},
            ],
        }

    # categorias
    return {
        "tipo_reporte": "categorias",
        "rango": periodo,
        "resumen": {"total_categorias": 4, "categoria_lider": "Pantalones"},
        "datos": [
            {"categoria": "Pantalones", "porcentaje": 42.0, "ingresos": 7749.0},
            {"categoria": "Abrigos", "porcentaje": 28.0, "ingresos": 5166.0},
            {"categoria": "Camisetas", "porcentaje": 18.0, "ingresos": 3321.0},
            {"categoria": "Calzado", "porcentaje": 12.0, "ingresos": 2214.0},
        ],
    }


def predecir_lote_textos(textos: List[str]) -> List[Dict[str, Any]]:
    """Procesa una lista de textos y retorna las predicciones individuales."""
    resultados = []
    for t in textos:
        intencion, prob, _ = predecir_intencion(t)
        resultados.append({
            "texto": t,
            "intencion": intencion,
            "probabilidad": prob,
        })
    return resultados
