"""Módulo de extracción de entidades para consultas de tiendas de ropa.

Responsable: Ramiro (Backend y NLP)
Propósito:
    Detectar atributos clave en la consulta del usuario mediante reglas heurísticas,
    expresiones regulares y coincidencia contra el catálogo de la tienda.
    Las entidades identificadas son:
      - talla: "M", "XL", "32", "38", etc.
      - color: "negro", "blanco", "azul", etc. (normalizado al singular masculino).
      - producto: "jeans", "polera", "chaqueta", etc.
      - categoria: "pantalones", "camisetas", "abrigos", etc.
      - fechas: expresiones temporales como "hoy", "esta semana", "octubre", etc.
"""

import re
import unicodedata
from typing import Any, Dict, List, Optional, Set, Tuple


def _quitar_tildes(texto: str) -> str:
    """Elimina tildes y diacríticos para facilitar búsquedas insensibles a acentos."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ------------------------------------------------------------------------------
# Diccionarios y léxicos base del dominio de tiendas de ropa
# ------------------------------------------------------------------------------

# Mapeo de variantes de colores hacia su forma canónica
COLORES_CANONICOS: Dict[str, str] = {
    "negro": "negro", "negra": "negro", "negros": "negro", "negras": "negro",
    "blanco": "blanco", "blanca": "blanco", "blancos": "blanco", "blancas": "blanco",
    "azul": "azul", "azules": "azul", "marino": "azul",
    "rojo": "rojo", "roja": "rojo", "rojos": "rojo", "rojas": "rojo",
    "verde": "verde", "verdes": "verde",
    "amarillo": "amarillo", "amarilla": "amarillo", "amarillos": "amarillo", "amarillas": "amarillo",
    "gris": "gris", "grises": "gris", "plomo": "gris", "ploma": "gris",
    "rosado": "rosado", "rosada": "rosado", "rosados": "rosado", "rosadas": "rosado", "rosa": "rosado",
    "cafe": "café", "marron": "café", "marrones": "café", "castano": "café",
    "beige": "beige", "crema": "beige",
    "morado": "morado", "morada": "morado", "morados": "morado", "moradas": "morado", "lila": "morado",
}

# Mapeo de prendas comunes y su categoría asociada
PRENDAS_BASE: Dict[str, Tuple[str, str]] = {
    # forma normalizada -> (nombre canónico de producto, categoría)
    "jean": ("jeans", "pantalones"),
    "jeans": ("jeans", "pantalones"),
    "pantalon": ("pantalón", "pantalones"),
    "pantalones": ("pantalón", "pantalones"),
    "polera": ("polera", "camisetas"),
    "poleras": ("polera", "camisetas"),
    "remera": ("polera", "camisetas"),
    "remeras": ("polera", "camisetas"),
    "camiseta": ("camiseta", "camisetas"),
    "camisetas": ("camiseta", "camisetas"),
    "camisa": ("camisa", "camisas"),
    "camisas": ("camisa", "camisas"),
    "chaqueta": ("chaqueta", "abrigos"),
    "chaquetas": ("chaqueta", "abrigos"),
    "chamarra": ("chamarra", "abrigos"),
    "chamarras": ("chamarra", "abrigos"),
    "abrigo": ("abrigo", "abrigos"),
    "abrigos": ("abrigo", "abrigos"),
    "campera": ("campera", "abrigos"),
    "camperas": ("campera", "abrigos"),
    "vestido": ("vestido", "vestidos"),
    "vestidos": ("vestido", "vestidos"),
    "falda": ("falda", "faldas"),
    "faldas": ("falda", "faldas"),
    "short": ("short", "pantalones cortos"),
    "shorts": ("short", "pantalones cortos"),
    "bermuda": ("bermuda", "pantalones cortos"),
    "bermudas": ("bermuda", "pantalones cortos"),
    "zapatilla": ("zapatillas", "calzado"),
    "zapatillas": ("zapatillas", "calzado"),
    "zapato": ("zapatos", "calzado"),
    "zapatos": ("zapatos", "calzado"),
    "botin": ("botines", "calzado"),
    "botines": ("botines", "calzado"),
    "bota": ("botas", "calzado"),
    "botas": ("botas", "calzado"),
}

# Léxico de expresiones temporales para consultas administrativas o envíos
EXPRESIONES_FECHAS: List[str] = [
    "esta semana", "la semana pasada", "semana actual", "la proxima semana",
    "este mes", "el mes pasado", "mes actual", "el proximo mes",
    "este ano", "el ano pasado", "este anio",
    "hoy", "ayer", "antier", "anteayer", "manana",
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
]


# ------------------------------------------------------------------------------
# Funciones auxiliares de detección
# ------------------------------------------------------------------------------

def _detectar_talla(texto_norm: str) -> Optional[str]:
    """Extrae tallas alfabéticas o numéricas comunes en confección de ropa."""
    # 1. Tallas compuestas o dobles primero: "s/m", "m/l", "xs/s", etc.
    patron_compuesta = re.search(r"\b(xs/s|s/m|m/l|l/xl)\b", texto_norm)
    if patron_compuesta:
        return patron_compuesta.group(1).upper()

    # 2. Tallas explícitas con prefijo: "talla 32", "talla-m", "talla xl", "en 38"
    patron_prefijo = re.search(
        r"\b(?:talla|tamano|numero|en|size)\s*[-:]?\s*([2-5][0-9]|xxl|2xl|3xl|xl|xs|[sml])\b",
        texto_norm,
    )
    if patron_prefijo:
        return patron_prefijo.group(1).upper()

    # 3. Tallas unívocas por letras compuestas (XL, XXL, XS) aunque no lleven la palabra "talla"
    patron_letras_claras = re.search(r"\b(xxl|2xl|3xl|xl|xs)\b", texto_norm)
    if patron_letras_claras:
        return patron_letras_claras.group(1).upper()

    # 4. Números de 2 cifras típicos de pantalones o calzado (28 a 52)
    patron_numero = re.search(r"\b([2-4][0-9]|50|52)\b", texto_norm)
    if patron_numero:
        return patron_numero.group(1)

    # 5. Letras aisladas (S, M, L) solo si están acompañadas de contexto de ropa/talla
    patron_letra_aislada = re.search(r"\b([sml])\b", texto_norm)
    if patron_letra_aislada and ("talla" in texto_norm or "ropa" in texto_norm or "polera" in texto_norm or "pantalon" in texto_norm):
        return patron_letra_aislada.group(1).upper()

    return None


def _detectar_color(texto_norm: str) -> Optional[str]:
    """Busca menciones de colores conocidos en el texto."""
    palabras = re.findall(r"\b[a-záéíóúñ]+\b", texto_norm)
    for palabra in palabras:
        if palabra in COLORES_CANONICOS:
            return COLORES_CANONICOS[palabra]
    return None


def _detectar_producto_y_categoria(
    texto_norm: str, catalogo: Optional[Dict[str, Any]] = None
) -> Tuple[Optional[str], Optional[str]]:
    """Detecta el nombre del producto y su categoría asociada contra el catálogo o base."""
    # 1. Si se provee catálogo específico de la tienda, buscar primero ahí
    if catalogo and isinstance(catalogo, dict):
        productos_catalogo = catalogo.get("productos", [])
        for item in productos_catalogo:
            nombre = item.get("nombre", "") if isinstance(item, dict) else str(item)
            nombre_norm = _quitar_tildes(nombre.lower())
            if nombre_norm and nombre_norm in texto_norm:
                cat = item.get("categoria") if isinstance(item, dict) else None
                return (nombre, cat)

        categorias_catalogo = catalogo.get("categorias", [])
        for cat in categorias_catalogo:
            cat_norm = _quitar_tildes(str(cat).lower())
            if cat_norm and cat_norm in texto_norm:
                return (None, str(cat))

    # 2. Búsqueda contra el léxico base de prendas
    palabras = re.findall(r"\b[a-záéíóúñ]+\b", texto_norm)
    for palabra in palabras:
        if palabra in PRENDAS_BASE:
            producto, categoria = PRENDAS_BASE[palabra]
            return (producto, categoria)

    return (None, None)


def _detectar_fechas(texto_norm: str) -> Optional[str]:
    """Identifica rangos o referencias de tiempo para consultas administrativas."""
    for expr in EXPRESIONES_FECHAS:
        if re.search(r"\b" + re.escape(expr) + r"\b", texto_norm):
            return expr

    # Expresión de fecha formato ISO AAAA-MM-DD o DD/MM/AAAA
    patron_fecha_iso = re.search(r"\b\d{4}-\d{2}-\d{2}\b", texto_norm)
    if patron_fecha_iso:
        return patron_fecha_iso.group(0)

    patron_fecha_slash = re.search(r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b", texto_norm)
    if patron_fecha_slash:
        return patron_fecha_slash.group(0)

    return None


# ------------------------------------------------------------------------------
# Función Principal del Módulo
# ------------------------------------------------------------------------------

def extraer_entidades(
    texto: str, catalogo: Optional[Dict[str, Any]] = None
) -> Dict[str, Optional[str]]:
    """Extrae entidades estructuradas a partir del texto de una consulta.

    Args:
        texto: Cadena de texto enviada por el usuario.
        catalogo: Diccionario opcional con productos y categorías importadas de la tienda.

    Returns:
        Diccionario con las entidades encontradas:
          {
            "talla": Optional[str],
            "color": Optional[str],
            "producto": Optional[str],
            "categoria": Optional[str],
            "fecha": Optional[str]
          }

    Ejemplo:
        >>> extraer_entidades("¿Tienen jeans negros en talla 32?")
        {'talla': '32', 'color': 'negro', 'producto': 'jeans', 'categoria': 'pantalones', 'fecha': None}
    """
    if not texto or not isinstance(texto, str):
        return {
            "talla": None,
            "color": None,
            "producto": None,
            "categoria": None,
            "fecha": None,
        }

    texto_normalizado = _quitar_tildes(texto.lower().strip())

    talla = _detectar_talla(texto_normalizado)
    color = _detectar_color(texto_normalizado)
    producto, categoria = _detectar_producto_y_categoria(texto_normalizado, catalogo)
    fecha = _detectar_fechas(texto_normalizado)

    return {
        "talla": talla,
        "color": color,
        "producto": producto,
        "categoria": categoria,
        "fecha": fecha,
    }
