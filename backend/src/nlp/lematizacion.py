"""Fase 4: Lematización y stemming.

Responsable: Fernando.
Funciones principales:
    lematizar(tokens) -> list[str]   spaCy (es_core_news_sm)
    stemmizar(tokens) -> list[str]   NLTK SnowballStemmer("spanish")

Las dos reducen cada palabra a una forma común para que el modelo vea como la
misma palabra "tienen", "tiene" y "tener":

    tokens:   tienen  jeans  negros  cuesta  abren
    lema:     tener   jean   negro   costar  abrir    (palabra real del diccionario)
    stem:     tien    jeans  negr    cuest   abren    (raíz recortada por reglas)

- Lematización: usa el contexto de la frase (sabe si "cuesta" es verbo) y
  devuelve palabras reales, más fáciles de explicar. Es más lenta y a veces se
  equivoca con texto informal ("dame" -> "damar").
- Stemming: aplica reglas fijas de recorte de sufijos. Es muy rápido y no
  necesita modelo, pero produce raíces que no son palabras y no reconoce
  formas irregulares ("abren" no se une con "abrir").

Cuál se usa en producción lo decide nlp.modo en src/config.yaml, según las
métricas de la comparación (notebook 02b).

Tallas ("m", "xl", "s/m") y números ("32", "12.50") se devuelven sin cambios:
son datos, no palabras que haya que reducir.

Correcciones de lema (LEMAS_FIJOS): es_core_news_sm se entrenó con noticias y
falla con palabras típicas de chat. Lo comprobamos así:
    "hola" -> "holar", "adios" -> "adio", "dame" -> "damar", "dale" -> "dalir",
    "gracias" -> a veces "gracia" y a veces "gracias" según la frase,
    "recomiendas" -> "recomiendir", "sugieres" -> "sugier", "sugiereme" -> "sugieremir".
Esas palabras reciben siempre el lema correcto. No son reglas de intención:
solo corrigen el lema para que la misma palabra no se parta en dos.
"""

import re
from functools import lru_cache
from typing import List

from src.nlp.normalizacion import normalizar

# Tallas en letras que deben pasar intactas por la lematización y el stemming
TALLAS = frozenset({"xxs", "xs", "s", "m", "l", "xl", "xxl", "xxxl"})

# Tokens con dígitos o barra (32, 12.50, s/m, 38/40) también pasan intactos
_DATO = re.compile(r"[\d/]")

# Lemas que spaCy calcula mal en texto de chat (ver docstring del módulo)
LEMAS_FIJOS = {
    "hola": "hola",
    "gracias": "gracias",
    "adios": "adios",
    "chau": "chau",
    "dame": "dar",
    "dale": "dar",
    # Verbos de recomendación (intención recomendar_productos): sin tilde spaCy
    # devuelve "recomiendir", "sugier", "sugieremir" o deja la forma sin reducir
    "recomiendas": "recomendar",
    "recomiendame": "recomendar",
    "recomiendeme": "recomendar",
    "recomendarias": "recomendar",
    "recomendaria": "recomendar",
    "sugieres": "sugerir",
    "sugiereme": "sugerir",
    "sugierame": "sugerir",
    "sugeririas": "sugerir",
    "aconsejas": "aconsejar",
    "aconsejame": "aconsejar",
}

MODELO_SPACY = "es_core_news_sm"


def _es_dato(token: str) -> bool:
    """True si el token es una talla o un número y no debe reducirse."""
    return token in TALLAS or bool(_DATO.search(token))


@lru_cache(maxsize=1)
def _get_spacy():
    """Carga el modelo de spaCy una sola vez; devuelve False si no está instalado."""
    try:
        import spacy

        # El parser y el reconocedor de entidades no hacen falta para lematizar:
        # se desactivan para que cargue y procese más rápido.
        return spacy.load(MODELO_SPACY, disable=["parser", "ner"])
    except (ImportError, OSError):
        return False


@lru_cache(maxsize=1)
def _get_stemmer():
    """Crea el stemmer Snowball en español una sola vez."""
    from nltk.stem import SnowballStemmer

    return SnowballStemmer("spanish")


@lru_cache(maxsize=20000)
def _lematizar_cached(tokens: tuple) -> tuple:
    """Lematiza una frase ya tokenizada; el resultado queda en caché.

    La caché importa en el entrenamiento: la validación cruzada transforma las
    mismas frases muchas veces y spaCy solo las procesa la primera vez.
    """
    nlp = _get_spacy()
    if not nlp:
        raise RuntimeError(
            f"No se encontró el modelo de spaCy '{MODELO_SPACY}'. "
            f"Instálalo con: python -m spacy download {MODELO_SPACY}"
        )

    from spacy.tokens import Doc

    # Se le pasan a spaCy los tokens ya separados (no el texto) para que devuelva
    # exactamente un lema por token y no vuelva a tokenizar a su manera.
    doc = nlp(Doc(nlp.vocab, words=list(tokens)))

    lemas = []
    for token, palabra in zip(tokens, doc):
        if _es_dato(token):
            lemas.append(token)  # tallas y números no se tocan
            continue
        if token in LEMAS_FIJOS:
            lemas.append(LEMAS_FIJOS[token])  # corrección de un error conocido de spaCy
            continue
        # spaCy puede devolver lemas con tilde ("él"); se normalizan igual que
        # los tokens para que "el" y "él" no sean palabras distintas.
        lema = normalizar(palabra.lemma_) or token
        # Verbos con pronombre pegado: "terminarse" -> "terminar él". Se conserva
        # solo el verbo; si no, aparecería un token "el" que no escribió el usuario.
        lemas.append(lema.split()[0])
    return tuple(lemas)


def lematizar(tokens: List[str]) -> List[str]:
    """Reduce cada token a su lema con spaCy.

    Recibe la frase completa (antes de quitar stop words) para que spaCy use el
    contexto al decidir si una palabra es verbo, sustantivo, etc.

    Ejemplo:
        >>> lematizar(["tienen", "jeans", "negros", "en", "talla", "32"])
        ['tener', 'jean', 'negro', 'en', 'talla', '32']
    """
    if not tokens:
        return []
    return list(_lematizar_cached(tuple(tokens)))


def stemmizar(tokens: List[str]) -> List[str]:
    """Recorta cada token a su raíz con el stemmer Snowball en español.

    Ejemplo:
        >>> stemmizar(["tienen", "jeans", "negros", "en", "talla", "32"])
        ['tien', 'jeans', 'negr', 'en', 'tall', '32']
    """
    stemmer = _get_stemmer()
    # Cada palabra se procesa sola: el stemming no usa contexto
    return [t if _es_dato(t) else stemmer.stem(t) for t in tokens]
