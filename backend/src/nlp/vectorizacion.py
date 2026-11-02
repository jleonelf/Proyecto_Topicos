"""Módulo de vectorización de texto con TF-IDF y N-gramas (Fase 5 - NLP).

Responsable: Ramiro
Propósito:
    Transformar texto limpio en representaciones vectoriales numéricas utilizando
    TF-IDF (Term Frequency - Inverse Document Frequency) y n-gramas (unigramas y bigramas).
    Este vectorizador se integra dentro del Pipeline final de scikit-learn
    junto con el preprocesamiento de texto y el clasificador.

Justificación técnica:
    1. TF-IDF vs CountVectorizer:
       CountVectorizer solo cuenta repeticiones, dando excesiva relevancia a términos
       frecuentes pero poco discriminantes. TF-IDF pondera positivamente las palabras
       que aparecen con frecuencia en una intención específica, penalizando aquellas
       que se distribuyen de manera uniforme a lo largo de todo el corpus.
    2. N-gramas (1, 1) vs (1, 2):
       En el dominio de tiendas de ropa, expresiones compuestas son críticas:
       "talla m", "jean negro", "sin stock", "envio gratis", "cuanto cuesta".
       Un modelo que solo analiza unigramas pierde la relación semántica de estas combinaciones.
       Configurar ngram_range=(1, 2) captura tanto términos individuales como pares contiguos.
    3. sublinear_tf=True:
       Reemplaza TF por 1 + log(TF), atenuando el impacto de palabras que se repiten
       múltiples veces en una misma consulta sin aportar el doble de significado.
    4. min_df y max_df:
       - min_df=1 (o 2): descarta errores tipográficos únicos o ruido estadístico.
       - max_df=0.95: descarta palabras presentes en más del 95% de las frases del corpus.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from sklearn.feature_extraction.text import TfidfVectorizer

try:
    from src.config import config as configuracion_global
except ImportError:
    configuracion_global = {}


def crear_vectorizador(config: Optional[Dict[str, Any]] = None) -> TfidfVectorizer:
    """Crea y configura una instancia de TfidfVectorizer según los parámetros especificados.

    Args:
        config: Diccionario con la configuración del vectorizador. Si no se proporciona
            o es None, se toma de la sección 'vectorizador' de src/config.yaml.

    Returns:
        TfidfVectorizer configurado y listo para ser ajustado (fit) o incluido en un Pipeline.

    Ejemplo:
        >>> from src.nlp.vectorizacion import crear_vectorizador
        >>> vectorizador = crear_vectorizador()
        >>> X = vectorizador.fit_transform(["tienen pantalones negros", "precio de polera"])
    """
    # Si no se pasó config, intentar extraer de la configuración global
    if config is None:
        cfg = configuracion_global.get("vectorizador", {})
    else:
        # Permite pasar el diccionario completo o solo la sección 'vectorizador'
        cfg = config.get("vectorizador", config)

    # Procesar ngram_range: asegurar que sea una tupla de dos enteros
    ngram_raw = cfg.get("ngram_range", (1, 2))
    if isinstance(ngram_raw, (list, tuple)) and len(ngram_raw) == 2:
        ngram_range: Tuple[int, int] = (int(ngram_raw[0]), int(ngram_raw[1]))
    else:
        ngram_range = (1, 2)

    min_df: Union[int, float] = cfg.get("min_df", 1)
    max_df: Union[int, float] = cfg.get("max_df", 0.95)
    max_features: Optional[int] = cfg.get("max_features", None)
    sublinear_tf: bool = bool(cfg.get("sublinear_tf", True))
    norm: Optional[str] = cfg.get("norm", "l2")
    use_idf: bool = bool(cfg.get("use_idf", True))

    # Instanciamos el vectorizador de scikit-learn
    vectorizador = TfidfVectorizer(
        ngram_range=ngram_range,
        min_df=min_df,
        max_df=max_df,
        max_features=max_features,
        sublinear_tf=sublinear_tf,
        norm=norm,
        use_idf=use_idf,
    )

    return vectorizador


def comparar_vocabulario_ngramas(
    corpus: List[str],
) -> Dict[str, Any]:
    """Compara el tamaño del vocabulario y los n-gramas generados con (1, 1) vs (1, 2).

    Útil para la demostración en notebooks y la defensa técnica.

    Args:
        corpus: Lista de textos para analizar.

    Returns:
        Diccionario con comparativa de vocabulario de unigramas vs unigramas+bigramas.
    """
    vec_unigramas = TfidfVectorizer(ngram_range=(1, 1))
    vec_bigramas = TfidfVectorizer(ngram_range=(1, 2))

    X_uni = vec_unigramas.fit_transform(corpus)
    X_bi = vec_bigramas.fit_transform(corpus)

    voc_uni = vec_unigramas.get_feature_names_out()
    voc_bi = vec_bigramas.get_feature_names_out()

    solo_bigramas = [token for token in voc_bi if " " in token]

    return {
        "num_unigramas": len(voc_uni),
        "num_total_con_bigramas": len(voc_bi),
        "num_bigramas_agregados": len(solo_bigramas),
        "ejemplos_bigramas": solo_bigramas[:10],
        "shape_unigramas": X_uni.shape,
        "shape_bigramas": X_bi.shape,
    }
