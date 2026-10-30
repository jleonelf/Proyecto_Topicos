"""Pipeline de Preprocesamiento NLP (Fases 1 a 4).

Responsable: Fernando (integración de fases 1 a 4 en transformer de scikit-learn).
"""

from typing import Dict, List, Any
from sklearn.base import BaseEstimator, TransformerMixin

from src.nlp.normalizacion import normalizar
from src.nlp.tokenizacion import tokenizar
from src.nlp.stopwords import quitar_stopwords
from src.nlp.lematizacion import lematizar, stemmizar


def preprocesar_pasos(
    texto: str,
    modo: str = "lema",
    stopwords_extra: List[str] = None,
    stopwords_exclude: List[str] = None
) -> Dict[str, Any]:
    """Ejecuta paso a paso el pipeline de NLP para mostrar en la interfaz.

    Devuelve un diccionario con el resultado de cada etapa.
    """
    paso_norm = normalizar(texto)
    paso_tokens = tokenizar(paso_norm)
    paso_sin_stop = quitar_stopwords(
        paso_tokens,
        extra=stopwords_extra,
        exclude=stopwords_exclude
    )

    if modo == "stem":
        paso_final = stemmizar(paso_sin_stop)
    else:
        paso_final = lematizar(paso_sin_stop)

    return {
        "original": texto,
        "normalizado": paso_norm,
        "tokens": paso_tokens,
        "sin_stopwords": paso_sin_stop,
        "resultado_tokens": paso_final,
        "resultado_texto": " ".join(paso_final),
        "modo": modo
    }


class TextPreprocessor(BaseEstimator, TransformerMixin):
    """Transformer compatible con scikit-learn Pipeline para texto en español."""

    def __init__(
        self,
        modo: str = "lema",
        stopwords_extra: List[str] = None,
        stopwords_exclude: List[str] = None
    ):
        self.modo = modo
        self.stopwords_extra = stopwords_extra
        self.stopwords_exclude = stopwords_exclude

    def fit(self, X, y=None):
        return self

    def transform(self, X, y=None) -> List[str]:
        """Procesa una colección de textos devolviendo strings limpios listos para TF-IDF."""
        resultados = []
        for texto in X:
            pasos = preprocesar_pasos(
                texto,
                modo=self.modo,
                stopwords_extra=self.stopwords_extra,
                stopwords_exclude=self.stopwords_exclude
            )
            resultados.append(pasos["resultado_texto"])
        return resultados
