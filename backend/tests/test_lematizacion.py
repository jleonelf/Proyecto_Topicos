"""Pruebas de la fase 4: lematización y stemming.

Responsable: Fernando.
"""

import pytest

from src.nlp import lematizacion
from src.nlp.lematizacion import lematizar, stemmizar


def test_lematizar_verbos_y_plurales():
    # Verbos conjugados -> infinitivo; plurales -> singular
    assert lematizar(["tienen", "jeans", "negros"]) == ["tener", "jean", "negro"]
    assert lematizar(["cuanto", "cuesta", "la", "chaqueta"])[1] == "costar"
    assert lematizar(["a", "que", "hora", "abren"])[-1] == "abrir"


def test_lematizar_devuelve_un_lema_por_token():
    tokens = ["que", "tallas", "hay", "de", "esta", "polera"]
    assert len(lematizar(tokens)) == len(tokens)


def test_lemas_sin_tildes():
    # spaCy lematiza "se"/"lo" como "él"; se normaliza a "el" igual que los tokens
    assert all("é" not in lema for lema in lematizar(["que", "productos", "se", "estan", "acabando"]))


def test_correcciones_de_palabras_de_chat():
    # Sin corrección spaCy da "holar" y "gracia"/"gracias" según el contexto
    assert lematizar(["hola", "buenas", "tardes"])[0] == "hola"
    assert lematizar(["muchas", "gracias"])[1] == "gracias"
    assert lematizar(["gracias", "chau"])[0] == "gracias"
    assert lematizar(["dame", "el", "reporte"])[0] == "dar"


@pytest.mark.parametrize("funcion", [lematizar, stemmizar])
def test_tallas_y_numeros_no_cambian(funcion):
    tokens = ["talla", "m", "xl", "s/m", "32", "12.50"]
    assert funcion(tokens)[1:] == ["m", "xl", "s/m", "32", "12.50"]


def test_stemmizar_recorta_sufijos():
    assert stemmizar(["tienen", "negros", "chaqueta"]) == ["tien", "negr", "chaquet"]


@pytest.mark.parametrize("funcion", [lematizar, stemmizar])
def test_lista_vacia(funcion):
    assert funcion([]) == []


def test_lematizar_usa_cache():
    lematizacion._lematizar_cached.cache_clear()
    lematizar(["hacen", "envios"])
    lematizar(["hacen", "envios"])
    assert lematizacion._lematizar_cached.cache_info().hits == 1


def test_error_claro_si_falta_spacy(monkeypatch):
    monkeypatch.setattr(lematizacion, "_get_spacy", lambda: False)
    lematizacion._lematizar_cached.cache_clear()
    with pytest.raises(RuntimeError, match="es_core_news_sm"):
        lematizar(["probando"])
    lematizacion._lematizar_cached.cache_clear()
