"""Fase 4: Lematización y Stemming.

Responsable: Fernando.
"""

from typing import List
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
            _nlp_spacy = spacy.load("es_core_news_sm")
        except Exception:
            _nlp_spacy = False
    return _nlp_spacy


def stemmizar(tokens: List[str]) -> List[str]:
    """Reduce cada token a su raíz usando el algoritmo Snowball (NLTK)."""
    return [_stemmer.stem(token) for token in tokens]


def lematizar(tokens: List[str]) -> List[str]:
    """Obtiene el lema canónico de cada token usando spaCy (con fallback a token original)."""
    nlp = _get_spacy()
    if nlp and nlp is not False:
        texto = " ".join(tokens)
        doc = nlp(texto)
        return [t.lemma_ for t in doc if not t.is_space]
    # Fallback si spaCy no tiene el modelo descargado
    return tokens
