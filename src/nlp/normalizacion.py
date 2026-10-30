"""Fase 1: Normalización de texto.

Responsable: Carmen.
"""

import re
import unicodedata


def normalizar(texto: str) -> str:
    """Normaliza el texto de entrada.

    - Convierte a minúsculas.
    - Elimina URLs.
    - Remueve caracteres de puntuación no informativos, conservando números
      y letras (tallas como '32', 'xl').
    - Limpia espacios repetidos.
    """
    if not isinstance(texto, str):
        return ""

    texto = texto.lower().strip()

    # Eliminar URLs
    texto = re.sub(r"https?://\S+|www\.\S+", " ", texto)

    # Eliminar signos de puntuación e interrogación/exclamación
    texto = re.sub(r"[¿?¡!.,;:\"'()[\]{}<>_`~#+*\/\\|-]", " ", texto)

    # Normalizar espacios en blanco
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto
