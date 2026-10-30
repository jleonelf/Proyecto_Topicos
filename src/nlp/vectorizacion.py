"""Fase 5: Vectorización con TF-IDF.

Responsable: Ramiro.
"""

from typing import Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer


def crear_vectorizador(config: Dict[str, Any]) -> TfidfVectorizer:
    """Instancia y configura un TfidfVectorizer según los parámetros dados."""
    v_cfg = config.get("vectorizer", {})

    ngram_range = tuple(v_cfg.get("ngram_range", [1, 2]))
    min_df = v_cfg.get("min_df", 1)
    max_df = v_cfg.get("max_df", 0.95)
    max_features = v_cfg.get("max_features", 2000)
    sublinear_tf = v_cfg.get("sublinear_tf", True)

    return TfidfVectorizer(
        ngram_range=ngram_range,
        min_df=min_df,
        max_df=max_df,
        max_features=max_features,
        sublinear_tf=sublinear_tf,
        lowercase=False  # Ya normalizado previamente en TextPreprocessor
    )
