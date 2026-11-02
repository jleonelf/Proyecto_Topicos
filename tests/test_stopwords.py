"""Pruebas de la fase 3: eliminación de stop words.

Responsable: Fernando.
"""

import pytest

from src.nlp.normalizacion import normalizar
from src.nlp.stopwords import lista_stopwords, quitar_stopwords
from src.nlp.tokenizacion import tokenizar


def _procesar(texto, **kwargs):
    return quitar_stopwords(tokenizar(normalizar(texto)), **kwargs)


def test_elimina_palabras_vacias():
    assert _procesar("quiero ver la chaqueta de cuero") == ["quiero", "chaqueta", "cuero"]


@pytest.mark.parametrize("texto, palabra", [
    ("no tienen jeans en talla 32", "no"),
    ("chaquetas sin stock", "sin"),
    ("algo más barato", "mas"),
    ("¿cuánto cuesta la polera?", "cuanto"),
    ("¿dónde queda la tienda?", "donde"),
    ("¿cómo puedo pagar?", "como"),
    ("¿cuáles tallas hay?", "cuales"),
    ("¿hay vestidos rojos?", "hay"),
    ("buenas tardes", "buenas"),
    ("buen día, necesito ayuda", "dia"),
    ("gracias, hasta luego", "luego"),
    ("productos con stock bajo", "bajo"),
    ("total vendido hoy", "total"),
])
def test_conserva_palabras_que_definen_la_intencion(texto, palabra):
    assert palabra in _procesar(texto)


def test_hola_y_gracias_no_son_stopwords():
    assert _procesar("hola, muchas gracias") == ["hola", "gracias"]


def test_elimina_muletillas_de_chat():
    assert _procesar("oye porfa dime el precio, por favor") == ["dime", "precio"]


def test_conserva_tallas_y_numeros():
    assert _procesar("talla m o s, la 32 o la s/m") == ["talla", "m", "s", "32", "s/m"]


def test_lista_spacy_sin_ajustes_borra_palabras_clave():
    resultado = _procesar("¿cuánto cuesta? no hay stock", lista="spacy")
    assert resultado == ["cuesta", "stock"]


def test_extra_y_excluir_desde_config():
    tokens = ["hola", "quiero", "jeans"]
    assert quitar_stopwords(tokens, extra=["quiero"]) == ["hola", "jeans"]
    assert "la" in quitar_stopwords(["la", "polera"], excluir=["la"])


def test_extra_con_tildes_y_mayusculas_se_normaliza():
    assert quitar_stopwords(["envio", "rapido"], extra=["Envío"]) == ["rapido"]


def test_lista_vacia_y_lista_invalida():
    assert quitar_stopwords([]) == []
    with pytest.raises(ValueError, match="lista debe ser"):
        lista_stopwords("inventada")


def test_lista_ajustada_es_mas_corta_que_spacy():
    assert len(lista_stopwords("ajustada")) < len(lista_stopwords("spacy"))
