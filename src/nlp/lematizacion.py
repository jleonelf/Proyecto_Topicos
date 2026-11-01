"""Fase 4: Lematización y Stemming.

Responsable: Fernando.
"""

from typing import List
import functools
import nltk
from nltk.stem.snowball import SnowballStemmer

# Stemmer para español
_stemmer = SnowballStemmer("spanish")

# Para spaCy, carga diferida (lazy load) para no penalizar el inicio rápido
_nlp_spacy = None


def _get_spacy():
    global _nlp_spacy
    if _nlp_spacy is None:
        try:
            import spacy
            _nlp_spacy = spacy.load("es_core_news_sm", disable=["parser", "ner"])
        except Exception:
            _nlp_spacy = False
    return _nlp_spacy


def stemmizar(tokens: List[str]) -> List[str]:
    """Reduce cada token a su raíz usando el algoritmo Snowball (NLTK)."""
    return [_stemmer.stem(token) for token in tokens]


@functools.lru_cache(maxsize=20000)
def _lematizar_cached(texto: str) -> tuple:
    nlp = _get_spacy()
    if not nlp or nlp is False:
        raise RuntimeError(
            "El modelo de spaCy 'es_core_news_sm' no está disponible. "
            "Para instalarlo, ejecute: python -m spacy download es_core_news_sm"
        )
    doc = nlp(texto)
    return tuple(t.lemma_ for t in doc if not t.is_space)


def lematizar(tokens: List[str]) -> List[str]:
    """Obtiene el lema canónico de cada token usando spaCy.

    Si el modelo es_core_news_sm no está disponible, lanza RuntimeError
    para evitar entrenar silenciosamente sin lematización.
    Utiliza caché LRU sobre la secuencia de tokens para acelerar la validación cruzada.
    """
    if not tokens:
        return []
    texto = " ".join(tokens)
    return list(_lematizar_cached(texto))
