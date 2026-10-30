"""Fase 3: Eliminación de Stop Words.

Responsable: Fernando.
"""

from typing import List, Optional, Set

# Lista base estándar en español
STOPWORDS_BASE_ES: Set[str] = {
    "de", "la", "que", "el", "en", "y", "a", "los", "del", "se", "las", "por", "un",
    "para", "con", "una", "su", "al", "lo", "como", "pero", "sus", "le", "ya", "o",
    "este", "sí", "porque", "esta", "entre", "cuando", "muy", "sobre", "también",
    "me", "hasta", "hay", "donde", "quien", "desde", "todo", "nos", "durante",
    "todos", "uno", "les", "ni", "contra", "otros", "ese", "eso", "ante", "ellos",
    "e", "esto", "mí", "antes", "algunos", "qué", "unos", "yo", "otro", "otras",
    "otra", "él", "tanto", "esa", "estos", "mucho", "quienes", "nada", "muchos",
    "cual", "poco", "ella", "estar", "estas", "algunas", "algo", "nosotros",
    "mi", "mis", "tus", "te", "ti", "tu"
}

# Palabras que NO deben eliminarse porque cambian el sentido de la consulta
DEFAULT_EXCLUDE: Set[str] = {"no", "sin", "más", "mas"}

# Palabras coloquiales que SÍ deben eliminarse
DEFAULT_EXTRA: Set[str] = {"porfa", "oye", "disculpa", "buenas", "hola", "favor"}


def quitar_stopwords(
    tokens: List[str],
    extra: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None
) -> List[str]:
    """Filtra la lista de tokens eliminando palabras vacías.

    Conserva negaciones y añade palabras de cortesía según la configuración.
    """
    stopwords = set(STOPWORDS_BASE_ES)

    if extra:
        stopwords.update(extra)
    else:
        stopwords.update(DEFAULT_EXTRA)

    if exclude:
        stopwords.difference_update(exclude)
    else:
        stopwords.difference_update(DEFAULT_EXCLUDE)

    return [token for token in tokens if token.lower() not in stopwords]
