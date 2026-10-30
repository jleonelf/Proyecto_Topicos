"""Fase 2: Tokenización de texto.

Responsable: Carmen.
"""

from typing import List
import re


def tokenizar(texto: str) -> List[str]:
    """Separa el texto en tokens/palabras respetando términos del dominio."""
    if not texto:
        return []

    # Extrae secuencias alfanuméricas
    tokens = re.findall(r"\b\w+\b", texto)
    return tokens
