"""Importación masiva del inventario (CSV o Excel) y analíticas de la tienda.

Responsable: Fernando (apartado "Inventarios y métricas").

Un archivo puede traer una o varias tablas. Cada tabla se reconoce por sus
columnas (formato estándar del plan, sección 3.2):

    productos   sku, nombre, categoria, talla, color, precio, stock
    ventas      fecha (YYYY-MM-DD), sku, cantidad, precio_unitario
    frases      texto, intencion       -> entrenamiento experimental del modelo

Un Excel puede tener varias hojas (por ejemplo "productos" y "ventas"); cada
hoja se importa según sus columnas. Los productos se importan antes que las
ventas, porque cada venta debe apuntar a un sku existente.

Las filas con errores no detienen la importación: se omiten y se informan con
su número de fila y el motivo, para que el usuario pueda corregirlas.
"""

import io
import unicodedata
from typing import Any, Dict, List, Tuple

import pandas as pd

from src.data.conexion import consultar, transaccion

# Columnas obligatorias de cada tipo de tabla
COLUMNAS = {
    "productos": {"sku", "nombre", "categoria", "precio"},
    "ventas": {"fecha", "sku", "cantidad", "precio_unitario"},
    "frases": {"texto", "intencion"},
}

# Orden de importación: los productos primero (las ventas los referencian)
ORDEN_TIPOS = ["productos", "ventas", "frases"]

MAX_BYTES = 5_000_000  # 5 MB por archivo
MAX_FILAS = 20_000  # filas por tabla
MAX_ERRORES_INFORMADOS = 50  # para no devolver miles de errores en la respuesta


class ArchivoInvalido(ValueError):
    """Error de formato del archivo completo (la API responde 400)."""


def _limpiar_columna(nombre: Any) -> str:
    """'Precio Unitario ' -> 'precio_unitario'; 'Categoría' -> 'categoria'."""
    texto = unicodedata.normalize("NFD", str(nombre).strip().lower())
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")  # quita tildes
    return texto.replace(" ", "_")


def leer_archivo(nombre: str, contenido: bytes) -> List[Tuple[str, pd.DataFrame]]:
    """Lee un .csv, .xlsx o .xls y devuelve una lista de (nombre_hoja, tabla)."""
    nombre = (nombre or "").lower()
    if len(contenido) == 0:
        raise ArchivoInvalido("El archivo está vacío.")
    if len(contenido) > MAX_BYTES:
        raise ArchivoInvalido("El archivo supera el máximo de 5 MB.")

    try:
        if nombre.endswith(".csv"):
            # utf-8-sig quita la marca BOM que agrega Excel al guardar como CSV;
            # sep=None detecta si el separador es coma o punto y coma
            texto = contenido.decode("utf-8-sig")
            hojas = [("csv", pd.read_csv(io.StringIO(texto), sep=None, engine="python", dtype=str))]
        elif nombre.endswith((".xlsx", ".xls")):
            # sheet_name=None lee todas las hojas del libro
            libro = pd.read_excel(io.BytesIO(contenido), sheet_name=None, dtype=str)
            hojas = list(libro.items())
        else:
            raise ArchivoInvalido("Formato no soportado: sube un archivo .csv, .xlsx o .xls.")
    except UnicodeDecodeError:
        raise ArchivoInvalido("El CSV debe estar codificado en UTF-8.") from None
    except ArchivoInvalido:
        raise
    except Exception as exc:
        raise ArchivoInvalido(f"No se pudo leer el archivo: {exc}") from None

    resultado = []
    for hoja, tabla in hojas:
        tabla.columns = [_limpiar_columna(c) for c in tabla.columns]
        tabla = tabla.dropna(how="all")  # filas completamente vacías
        resultado.append((str(hoja), tabla))
    return resultado


def detectar_tipo(tabla: pd.DataFrame) -> str:
    """Devuelve 'productos', 'ventas' o 'frases' según las columnas de la tabla."""
    columnas = set(tabla.columns)
    for tipo in ORDEN_TIPOS:
        if COLUMNAS[tipo] <= columnas:  # están todas las columnas obligatorias
            return tipo
    esperado = "; ".join(f"{t}: {', '.join(sorted(c))}" for t, c in COLUMNAS.items())
    raise ArchivoInvalido(
        f"No se reconocen las columnas {sorted(columnas)}. Columnas esperadas -> {esperado}."
    )


def _texto(valor: Any) -> str:
    """Convierte una celda en texto limpio ('' si está vacía)."""
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return ""
    return str(valor).strip()


def _numero(valor: Any) -> float:
    """Convierte '1.250,50' o '1250.50' en 1250.5; lanza ValueError si no es número."""
    texto = _texto(valor).replace(" ", "")
    if "," in texto and "." in texto:
        texto = texto.replace(".", "").replace(",", ".")  # formato 1.250,50
    else:
        texto = texto.replace(",", ".")  # formato 1250,50
    return float(texto)


def _validar_productos(tabla: pd.DataFrame) -> Tuple[List[tuple], List[Dict[str, Any]]]:
    """Valida cada fila de productos; devuelve (filas_validas, errores)."""
    validas: Dict[str, tuple] = {}  # por sku: si se repite, gana la última fila
    errores = []
    for i, fila in enumerate(tabla.to_dict("records"), start=2):  # fila 1 = encabezado
        try:
            sku = _texto(fila.get("sku"))
            nombre = _texto(fila.get("nombre"))
            categoria = _texto(fila.get("categoria")).lower()
            if not sku or not nombre or not categoria:
                raise ValueError("faltan sku, nombre o categoria")
            precio = _numero(fila.get("precio"))
            stock_txt = _texto(fila.get("stock"))
            stock = int(_numero(stock_txt)) if stock_txt else 0  # sin stock informado -> 0
            if precio < 0 or stock < 0:
                raise ValueError("precio y stock no pueden ser negativos")
            talla = _texto(fila.get("talla")).upper() or None
            color = _texto(fila.get("color")).lower() or None
            validas[sku] = (sku, nombre, categoria, talla, color, round(precio, 2), stock)
        except ValueError as exc:
            errores.append({"fila": i, "motivo": str(exc)})
    return list(validas.values()), errores


def _validar_ventas(tabla: pd.DataFrame, skus_existentes: set) -> Tuple[List[tuple], List[Dict[str, Any]]]:
    """Valida cada fila de ventas; el sku debe existir en productos."""
    validas, errores = [], []
    for i, fila in enumerate(tabla.to_dict("records"), start=2):
        try:
            fecha = pd.to_datetime(_texto(fila.get("fecha")), errors="coerce")
            if pd.isna(fecha):
                raise ValueError("fecha inválida (usar YYYY-MM-DD)")
            sku = _texto(fila.get("sku"))
            if sku not in skus_existentes:
                raise ValueError(f"el sku '{sku}' no existe en productos")
            cantidad = int(_numero(fila.get("cantidad")))
            precio = _numero(fila.get("precio_unitario"))
            if cantidad <= 0 or precio < 0:
                raise ValueError("cantidad debe ser mayor que 0 y precio_unitario no negativo")
            validas.append((fecha.date().isoformat(), sku, cantidad, round(precio, 2)))
        except ValueError as exc:
            errores.append({"fila": i, "motivo": str(exc)})
    return validas, errores


def _skus_en_base() -> set:
    """SKU ya guardados (si la base aún no tiene tablas, devuelve vacío)."""
    try:
        return {fila["sku"] for fila in consultar("SELECT sku FROM productos")}
    except Exception:
        return set()


def importar_tablas(hojas: List[Tuple[str, pd.DataFrame]], reemplazar: bool = False) -> Dict[str, Any]:
    """Valida e importa las tablas de inventario de un archivo.

    reemplazar=True borra las ventas (y productos sin ventas) anteriores antes
    de importar; con False se agregan a las existentes y los productos con el
    mismo sku se actualizan.

    Devuelve un resumen por hoja y las tablas de frases (que no van a la base,
    sino al entrenamiento experimental).
    """
    por_tipo = {tipo: [] for tipo in ORDEN_TIPOS}
    for hoja, tabla in hojas:
        if len(tabla) > MAX_FILAS:
            raise ArchivoInvalido(f"La hoja '{hoja}' tiene {len(tabla)} filas; el máximo es {MAX_FILAS}.")
        por_tipo[detectar_tipo(tabla)].append((hoja, tabla))

    resumen = []
    # Si se reemplazan los productos, los SKU válidos son solo los del archivo
    skus = set() if (reemplazar and por_tipo["productos"]) else _skus_en_base()

    with transaccion() as t:  # todo o nada: si algo falla, no queda una importación a medias
        if reemplazar:
            t.ejecutar("DELETE FROM ventas")
            if por_tipo["productos"]:
                t.ejecutar("DELETE FROM productos")

        for hoja, tabla in por_tipo["productos"]:
            filas, errores = _validar_productos(tabla)
            # ON CONFLICT: si el sku ya existe se actualiza en lugar de duplicarse
            t.ejecutar_muchos(
                "INSERT INTO productos (sku, nombre, categoria, talla, color, precio, stock) "
                "VALUES (?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT (sku) DO UPDATE SET nombre = excluded.nombre, categoria = excluded.categoria, "
                "talla = excluded.talla, color = excluded.color, precio = excluded.precio, stock = excluded.stock",
                filas,
            )
            skus |= {f[0] for f in filas}
            resumen.append(_resumen_hoja(hoja, "productos", tabla, filas, errores))

        for hoja, tabla in por_tipo["ventas"]:
            filas, errores = _validar_ventas(tabla, skus)
            t.ejecutar_muchos(
                "INSERT INTO ventas (fecha, sku, cantidad, precio_unitario) VALUES (?, ?, ?, ?)", filas
            )
            resumen.append(_resumen_hoja(hoja, "ventas", tabla, filas, errores))

    frases = [tabla for _, tabla in por_tipo["frases"]]
    for hoja, tabla in por_tipo["frases"]:
        resumen.append({"hoja": hoja, "tipo": "frases", "filas_leidas": len(tabla),
                        "filas_importadas": 0, "filas_omitidas": 0, "errores": []})
    return {"hojas": resumen, "frases": frases}


def _resumen_hoja(hoja, tipo, tabla, filas, errores) -> Dict[str, Any]:
    """Resumen de una hoja importada para la respuesta de la API."""
    return {
        "hoja": hoja,
        "tipo": tipo,
        "filas_leidas": len(tabla),
        "filas_importadas": len(filas),
        "filas_omitidas": len(errores),
        "errores": errores[:MAX_ERRORES_INFORMADOS],
    }


# ------------------------------------------------------------------------------
# Analíticas del inventario (para el apartado "Inventarios y métricas")
# Las consultas usan SQL estándar: funcionan igual en PostgreSQL y SQLite.
# ------------------------------------------------------------------------------

def _flotante(valor: Any) -> float:
    """Decimal/None de la base -> float redondeado."""
    return round(float(valor or 0), 2)


def resumen_inventario(umbral_stock: int = 5, limite: int = 10) -> Dict[str, Any]:
    """Indicadores, rankings y series del inventario y las ventas."""
    try:
        prod = consultar(
            "SELECT COUNT(*) AS productos, COALESCE(SUM(stock), 0) AS unidades, "
            "COALESCE(SUM(precio * stock), 0) AS valor, COUNT(DISTINCT categoria) AS categorias FROM productos"
        )[0]
    except Exception:
        # La base no existe o no tiene tablas todavía
        return {"disponible": False, "motivo": "La base de datos no está disponible o no tiene tablas."}

    ventas = consultar(
        "SELECT COALESCE(SUM(cantidad * precio_unitario), 0) AS ingresos, COALESCE(SUM(cantidad), 0) AS unidades, "
        "COUNT(*) AS transacciones, MIN(fecha) AS desde, MAX(fecha) AS hasta FROM ventas"
    )[0]
    transacciones = int(ventas["transacciones"])
    ingresos = _flotante(ventas["ingresos"])

    mas_vendidos = consultar(
        "SELECT p.nombre, p.categoria, SUM(v.cantidad) AS unidades, SUM(v.cantidad * v.precio_unitario) AS ingresos "
        "FROM ventas v JOIN productos p ON p.sku = v.sku "
        "GROUP BY p.nombre, p.categoria ORDER BY unidades DESC LIMIT ?",
        (limite,),
    )
    por_categoria = consultar(
        "SELECT p.categoria, SUM(v.cantidad) AS unidades, SUM(v.cantidad * v.precio_unitario) AS ingresos "
        "FROM ventas v JOIN productos p ON p.sku = v.sku GROUP BY p.categoria ORDER BY ingresos DESC"
    )
    por_fecha = consultar(
        "SELECT fecha, SUM(cantidad * precio_unitario) AS ingresos, SUM(cantidad) AS unidades "
        "FROM ventas GROUP BY fecha ORDER BY fecha"
    )
    stock_bajo = consultar(
        "SELECT sku, nombre, categoria, talla, color, stock FROM productos WHERE stock <= ? "
        "ORDER BY stock ASC, nombre LIMIT 50",
        (umbral_stock,),
    )
    stock_categoria = consultar(
        "SELECT categoria, COUNT(*) AS productos, SUM(stock) AS unidades FROM productos "
        "GROUP BY categoria ORDER BY unidades DESC"
    )

    return {
        "disponible": True,
        "indicadores": {
            "productos": int(prod["productos"]),
            "unidades_en_stock": int(prod["unidades"]),
            "valor_inventario": _flotante(prod["valor"]),
            "categorias": int(prod["categorias"]),
            "ingresos": ingresos,
            "unidades_vendidas": int(ventas["unidades"]),
            "transacciones": transacciones,
            "ticket_promedio": round(ingresos / transacciones, 2) if transacciones else 0.0,
            "desde": str(ventas["desde"]) if ventas["desde"] else None,
            "hasta": str(ventas["hasta"]) if ventas["hasta"] else None,
        },
        "umbral_stock": umbral_stock,
        "mas_vendidos": [
            {"nombre": f["nombre"], "categoria": f["categoria"], "unidades": int(f["unidades"]),
             "ingresos": _flotante(f["ingresos"])} for f in mas_vendidos
        ],
        "ventas_por_categoria": [
            {"categoria": f["categoria"], "unidades": int(f["unidades"]), "ingresos": _flotante(f["ingresos"])}
            for f in por_categoria
        ],
        "ventas_por_fecha": [
            {"fecha": str(f["fecha"]), "ingresos": _flotante(f["ingresos"]), "unidades": int(f["unidades"])}
            for f in por_fecha
        ],
        "stock_bajo": [dict(f, stock=int(f["stock"])) for f in stock_bajo],
        "stock_por_categoria": [
            {"categoria": f["categoria"], "productos": int(f["productos"]), "unidades": int(f["unidades"] or 0)}
            for f in stock_categoria
        ],
    }
