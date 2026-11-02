"""Pruebas unitarias para el módulo de vectorización (Fase 5 - NLP).

Responsable: Ramiro
"""

import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from src.nlp.vectorizacion import crear_vectorizador, comparar_vocabulario_ngramas


@pytest.fixture
def corpus_ropa():
    """Corpus de prueba con expresiones típicas de clientes de tiendas de ropa."""
    return [
        "tienen jeans negros en talla 32",
        "cuanto cuesta la chaqueta de cuero",
        "que tallas hay de esta polera",
        "tienen stock de polera en talla m",
        "hacen envios a domicilio en cochabamba",
        "quiero cambiar un pantalon que no me queda bien",
    ]


def test_crear_vectorizador_instancia_correcta():
    """Verifica que se instancie un TfidfVectorizer con la configuración global."""
    vec = crear_vectorizador()
    assert isinstance(vec, TfidfVectorizer)
    # Por defecto en config.yaml debe ser (1, 2)
    assert vec.ngram_range == (1, 2)
    assert vec.sublinear_tf is True
    assert vec.norm == "l2"
    assert vec.use_idf is True


def test_crear_vectorizador_config_personalizada():
    """Verifica que acepte un diccionario personalizado de parámetros."""
    config_custom = {
        "vectorizador": {
            "ngram_range": [1, 1],
            "min_df": 2,
            "max_df": 0.8,
            "max_features": 100,
            "sublinear_tf": False,
            "norm": "l1",
            "use_idf": False,
        }
    }
    vec = crear_vectorizador(config_custom)
    assert vec.ngram_range == (1, 1)
    assert vec.min_df == 2
    assert vec.max_df == 0.8
    assert vec.max_features == 100
    assert vec.sublinear_tf is False
    assert vec.norm == "l1"
    assert vec.use_idf is False


def test_vectorizador_ajuste_y_transformacion(corpus_ropa):
    """Verifica que el vectorizador ajuste (fit) y transforme correctamente el corpus."""
    vec = crear_vectorizador()
    matriz_tfidf = vec.fit_transform(corpus_ropa)

    # Debe ser una matriz dispersa con tantas filas como frases
    assert matriz_tfidf.shape[0] == len(corpus_ropa)
    assert matriz_tfidf.shape[1] > 0

    vocabulario = vec.get_feature_names_out()
    # Debe contener tanto unigramas como bigramas
    tiene_unigramas = any(" " not in termino for termino in vocabulario)
    tiene_bigramas = any(" " in termino for termino in vocabulario)

    assert tiene_unigramas, "El vocabulario debe contener unigramas"
    assert tiene_bigramas, "El vocabulario debe contener bigramas como 'talla 32' o 'chaqueta de'"


def test_comparar_vocabulario_ngramas(corpus_ropa):
    """Verifica la función comparativa entre unigramas y unigramas + bigramas."""
    resultado = comparar_vocabulario_ngramas(corpus_ropa)

    assert "num_unigramas" in resultado
    assert "num_total_con_bigramas" in resultado
    assert "num_bigramas_agregados" in resultado
    assert resultado["num_total_con_bigramas"] > resultado["num_unigramas"]
    assert resultado["num_bigramas_agregados"] > 0
    assert len(resultado["ejemplos_bigramas"]) > 0


def test_manejo_ngram_range_invalido():
    """Verifica que maneje de forma segura entradas atípicas de ngram_range."""
    config_invalido = {"ngram_range": "invalido"}
    vec = crear_vectorizador(config_invalido)
    # Debe retroceder al valor por defecto (1, 2) sin lanzar excepción
    assert vec.ngram_range == (1, 2)
