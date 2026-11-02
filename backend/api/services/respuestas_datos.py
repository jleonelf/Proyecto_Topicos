"""Respuestas del chatbot con los datos reales de la tienda importados en la base.

Responsable: Fernando.

El modelo decide la INTENCIÓN y el extractor de Ramiro las ENTIDADES (producto,
talla, color). Este módulo usa ambas para consultar la base y responder con datos
reales: stock y precio del producto pedido, tallas disponibles, horarios,
envíos, devoluciones, pagos y reportes de administración.

Si la base no tiene los datos que hacen falta, devuelve None y el chat usa las
plantillas fijas de chat_service.py, como antes.
"""

from typing import Any, Dict, List, Optional

from src.data.inventario import datos_tienda, productos_en_base, resumen_inventario
from src.nlp.normalizacion import normalizar

MAX_VARIANTES = 4  # variantes que se mencionan como máximo en una respuesta


def _bs(valor: float) -> str:
    """250.0 -> 'Bs 250'; 80.5 -> 'Bs 80.50'."""
    return f"Bs {valor:,.0f}" if float(valor).is_integer() else f"Bs {valor:,.2f}"


def _raiz(palabra: str) -> str:
    """Forma comparable de una palabra: sin tildes, minúsculas y sin plural final.

    "Jeans" -> "jean", "poleras" -> "polera", "pantalones" -> "pantalon".
    """
    p = normalizar(palabra or "")
    if p.endswith("es") and len(p) > 5:
        return p[:-2]
    return p[:-1] if p.endswith("s") and len(p) > 3 else p


def _buscar(productos: List[Dict[str, Any]], entidades: Dict[str, Optional[str]]) -> List[Dict[str, Any]]:
    """Productos que coinciden con la prenda o categoría pedida (sin filtrar talla/color).

    Primero se busca por la prenda ("jeans"); solo si no hay coincidencias se usa
    la categoría ("pantalones"), para no responder con todos los pantalones
    cuando se preguntó por jeans.
    """
    for clave in (_raiz(entidades.get("producto")), _raiz(entidades.get("categoria"))):
        if not clave:
            continue
        # Coincide si la raíz de lo pedido aparece en el nombre o en la categoría del producto
        encontrados = [p for p in productos if clave in normalizar(p["nombre"]) or clave in normalizar(p["categoria"])]
        if encontrados:
            return encontrados
    return []


def _filtrar(productos: List[Dict[str, Any]], talla: Optional[str], color: Optional[str]) -> List[Dict[str, Any]]:
    """Filtra por talla y color (comparación sin mayúsculas ni tildes)."""
    if talla:
        productos = [p for p in productos if normalizar(p.get("talla") or "") == normalizar(talla)]
    if color:
        productos = [p for p in productos if normalizar(p.get("color") or "") == normalizar(color)]
    return productos


def _describir(p: Dict[str, Any]) -> str:
    """'Jean Slim talla 32 negro'."""
    partes = [p["nombre"]]
    if p.get("talla"):
        partes.append(f"talla {p['talla']}")
    if p.get("color"):
        partes.append(p["color"])
    return " ".join(partes)


def _lista(valores) -> str:
    """['32', '34', '36'] -> '32, 34 y 36'."""
    valores = list(dict.fromkeys(v for v in valores if v))  # sin repetidos, en orden
    if len(valores) <= 1:
        return "".join(valores)
    return ", ".join(valores[:-1]) + " y " + valores[-1]


def _pedido(entidades: Dict[str, Optional[str]]) -> str:
    """Texto de lo que pidió el cliente: 'jeans negro en talla 32'."""
    texto = entidades.get("producto") or entidades.get("categoria") or "esa prenda"
    if entidades.get("color"):
        texto += f" {entidades['color']}"
    if entidades.get("talla"):
        texto += f" en talla {entidades['talla']}"
    return texto


# ------------------------------------------------------------------------------
# Intenciones de cliente sobre productos
# ------------------------------------------------------------------------------

def _stock(productos, entidades) -> Optional[str]:
    candidatos = _buscar(productos, entidades)
    if not candidatos:
        if entidades.get("producto") or entidades.get("categoria"):
            categorias = _lista(sorted({p["categoria"] for p in productos}))
            return f"No encontré {_pedido(entidades)} en nuestro catálogo. Tenemos: {categorias}."
        return None  # no dijo qué prenda: mejor la plantilla que pregunta

    exactos = [p for p in _filtrar(candidatos, entidades.get("talla"), entidades.get("color")) if p["stock"] > 0]
    if exactos:
        detalle = "; ".join(f"{_describir(p)}: {p['stock']} unid. a {_bs(p['precio'])}" for p in exactos[:MAX_VARIANTES])
        return f"¡Sí! Tenemos disponible {detalle}."

    # No hay lo exacto: se ofrecen las alternativas con stock de esa prenda
    alternativas = [p for p in candidatos if p["stock"] > 0]
    if not alternativas:
        return f"Por ahora no tenemos {_pedido(entidades)} en stock. ¿Te aviso cuando repongamos?"
    tallas = _lista(p.get("talla") for p in alternativas)
    colores = _lista(p.get("color") for p in alternativas)
    sugerencia = " y ".join(x for x in [f"tallas {tallas}" if tallas else "", f"colores {colores}" if colores else ""] if x)
    return f"No nos queda {_pedido(entidades)}, pero sí tenemos {alternativas[0]['nombre']} en {sugerencia}."


def _precio(productos, entidades) -> Optional[str]:
    candidatos = _filtrar(_buscar(productos, entidades), entidades.get("talla"), entidades.get("color"))
    if not candidatos:
        return None
    # Agrupa por nombre: cada prenda con su rango de precios entre variantes
    por_nombre: Dict[str, List[float]] = {}
    for p in candidatos:
        por_nombre.setdefault(p["nombre"], []).append(p["precio"])
    partes = []
    for nombre, precios in list(por_nombre.items())[:MAX_VARIANTES]:
        minimo, maximo = min(precios), max(precios)
        partes.append(f"{nombre}: {_bs(minimo)}" if minimo == maximo else f"{nombre}: de {_bs(minimo)} a {_bs(maximo)}")
    return "Estos son los precios: " + "; ".join(partes) + "."


def _tallas(productos, entidades) -> Optional[str]:
    candidatos = [p for p in _filtrar(_buscar(productos, entidades), None, entidades.get("color")) if p["stock"] > 0]
    if not candidatos:
        return None
    por_nombre: Dict[str, List[str]] = {}
    for p in candidatos:
        por_nombre.setdefault(p["nombre"], []).append(p.get("talla") or "única")
    partes = [f"{nombre}: {_lista(tallas)}" for nombre, tallas in list(por_nombre.items())[:MAX_VARIANTES]]
    return "Tallas disponibles ahora: " + "; ".join(partes) + "."


# ------------------------------------------------------------------------------
# Respuesta principal
# ------------------------------------------------------------------------------

def responder_con_datos(intencion: str, entidades: Dict[str, Optional[str]]) -> Optional[str]:
    """Respuesta con datos reales de la base, o None si no hay datos para esa intención."""
    entidades = entidades or {}

    if intencion in ("consultar_stock", "consultar_precio", "consultar_tallas"):
        productos = productos_en_base()
        if not productos:
            return None
        funcion = {"consultar_stock": _stock, "consultar_precio": _precio, "consultar_tallas": _tallas}[intencion]
        return funcion(productos, entidades)

    if intencion in ("saludo", "envios", "devoluciones", "horarios_ubicacion", "metodos_pago"):
        tienda = datos_tienda()
        if not tienda:
            return None
        if intencion == "saludo":
            return f"¡Hola! Bienvenido a {tienda['nombre']}. ¿En qué te puedo ayudar hoy?"
        if intencion == "horarios_ubicacion":
            return f"Atendemos {tienda['horarios']}. Nos encuentras en {tienda['direccion']}."
        textos = {"envios": tienda["envios"], "devoluciones": tienda["devoluciones"],
                  "metodos_pago": f"Aceptamos: {tienda['metodos_pago']}."}
        return textos[intencion] or None

    if intencion in ("reporte_ventas", "productos_mas_vendidos", "stock_bajo", "ventas_por_categoria"):
        return _reporte(intencion)

    return None


def _reporte(intencion: str) -> Optional[str]:
    """Respuestas de administración con las analíticas del inventario."""
    datos = resumen_inventario()
    if not datos.get("disponible") or datos["indicadores"]["productos"] == 0:
        return None
    ind = datos["indicadores"]
    periodo = f"del {ind['desde']} al {ind['hasta']}" if ind["desde"] else "registrado"

    if intencion == "reporte_ventas":
        if not ind["transacciones"]:
            return "Todavía no hay ventas registradas."
        return (f"Ventas {periodo}: {ind['transacciones']} ventas, {ind['unidades_vendidas']} unidades y "
                f"{_bs(ind['ingresos'])} en ingresos (ticket promedio {_bs(ind['ticket_promedio'])}).")

    if intencion == "productos_mas_vendidos":
        top = datos["mas_vendidos"][:3]
        if not top:
            return "Todavía no hay ventas registradas."
        return f"Más vendidos {periodo}: " + ", ".join(f"{i}. {p['nombre']} ({p['unidades']} unid.)" for i, p in enumerate(top, 1)) + "."

    if intencion == "stock_bajo":
        bajos = datos["stock_bajo"]
        if not bajos:
            return f"Ningún producto tiene {datos['umbral_stock']} unidades o menos."
        detalle = ", ".join(f"{_describir(p)} ({p['stock']} unid.)" for p in bajos[:5])
        return f"Hay {len(bajos)} productos con stock bajo (≤ {datos['umbral_stock']}): {detalle}."

    # ventas_por_categoria
    categorias = datos["ventas_por_categoria"]
    if not categorias:
        return "Todavía no hay ventas registradas."
    total = sum(c["ingresos"] for c in categorias) or 1
    return f"Ventas por categoría {periodo}: " + ", ".join(
        f"{c['categoria']} {c['ingresos'] / total:.0%} ({_bs(c['ingresos'])})" for c in categorias[:5]
    ) + "."
