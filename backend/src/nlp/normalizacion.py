"""Fase 1: Normalización del texto.

Responsable: Carmen.
Función principal: normalizar(texto) -> str

Qué se elimina:
    - Mayúsculas (todo a minúsculas).
    - Tildes y diéresis (á -> a, ü -> u). La "ñ" se conserva porque cambia
      el significado ("año" no es "ano", "pequeño" no es "pequeno").
    - URLs, correos y menciones (@usuario): no aportan a la intención.
    - Emojis y símbolos: en consultas de una tienda de ropa casi nunca
      definen la intención.
    - Signos de puntuación (¿?¡!.,;:"()...).
    - Apóstrofos dentro de palabras: "jean's" -> "jeans".

Qué se conserva:
    - Números, porque son tallas ("32") o precios ("100bs").
    - Decimales ("12.50") y la barra entre letras ("s/m"), que la
      tokenización trata como una sola unidad.
    - El guion entre palabras ("talla-m"); la tokenización lo separa.
"""

import re
import unicodedata

_URL = re.compile(r"(https?://\S+|www\.\S+)")
_EMAIL = re.compile(r"\S+@\S+\.\S+")
_MENCION = re.compile(r"@\w+")
_APOSTROFO = re.compile(r"(?<=[a-zñ])['’´`](?=[a-zñ])")
_DECIMAL = re.compile(r"(?<=\d)[.,](?=\d)")
_BARRA = re.compile(r"(?<=[a-zñ0-9])/(?=[a-zñ0-9])")
_GUION = re.compile(r"(?<=[a-zñ0-9])-(?=[a-zñ0-9])")
_NO_PERMITIDO = re.compile(r"[^a-zñ0-9\s\x00\x01\x02]")
_ESPACIOS = re.compile(r"\s+")

# Marcadores temporales para proteger caracteres que no deben borrarse
_M_DECIMAL, _M_BARRA, _M_GUION = "\x00", "\x01", "\x02"


def _quitar_tildes(texto: str) -> str:
    """Quita tildes y diéresis conservando la ñ."""
    texto = texto.replace("ñ", "\x03")
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )
    return sin_tildes.replace("\x03", "ñ")


def normalizar(texto: str) -> str:
    """Normaliza un texto en español para el pipeline de NLP.

    Ejemplo:
        >>> normalizar("¿Tienen JEAN'S en Talla-M? 😍 https://tienda.com")
        'tienen jeans en talla-m'
    """
    if not isinstance(texto, str):
        return ""

    t = texto.lower()
    t = _URL.sub(" ", t)
    t = _EMAIL.sub(" ", t)
    t = _MENCION.sub(" ", t)
    t = _quitar_tildes(t)
    t = _APOSTROFO.sub("", t)

    t = _DECIMAL.sub(_M_DECIMAL, t)
    t = _BARRA.sub(_M_BARRA, t)
    t = _GUION.sub(_M_GUION, t)
    t = _NO_PERMITIDO.sub(" ", t)
    t = t.replace(_M_DECIMAL, ".").replace(_M_BARRA, "/").replace(_M_GUION, "-")

    return _ESPACIOS.sub(" ", t).strip()
