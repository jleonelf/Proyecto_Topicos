"""Fase 2: Tokenización del texto.

Responsable: Carmen.
Función principal: tokenizar(texto) -> list[str]

Recibe el texto ya normalizado (salida de la fase 1) y lo divide en tokens.
Casos difíciles del dominio (tiendas de ropa):
    - "talla-m"  -> ["talla", "m"]   el guion separa palabra y talla
    - "xl"       -> ["xl"]           tallas en letras quedan como un token
    - "s/m"      -> ["s/m"]          talla combinada: un solo token
    - "100bs"    -> ["100", "bs"]    precio y moneda por separado
    - "12.50"    -> ["12.50"]        decimales no se parten
    - "jeans"    -> ["jeans"]        ("jean's" ya llega sin apóstrofo)
"""

import re
from typing import List

# Orden importa: primero las tallas con barra, luego números y por último palabras.
_TOKEN = re.compile(
    r"[a-zñ0-9]+/[a-zñ0-9]+"   # tallas combinadas: s/m, 38/40
    r"|\d+(?:\.\d+)?"          # números enteros o decimales: 32, 12.50
    r"|[a-zñ]+"                # palabras: talla, xl, bs
)


def tokenizar(texto: str) -> List[str]:
    """Divide un texto normalizado en una lista de tokens.

    Ejemplo:
        >>> tokenizar("jeans talla-m a 100bs en s/m")
        ['jeans', 'talla', 'm', 'a', '100', 'bs', 'en', 's/m']
    """
    if not isinstance(texto, str):
        return []
    return _TOKEN.findall(texto)
