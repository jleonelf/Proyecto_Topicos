"""Pruebas de la unión de fases 1 a 4 (TextPreprocessor y preprocesar_pasos).

Responsable: Fernando.
"""

import pytest
from sklearn.base import clone

from src.nlp.pipeline import TextPreprocessor, crear_preprocesador, preprocesar_pasos


def test_transform_devuelve_texto_final_por_frase():
    prep = TextPreprocessor(modo="lema").fit([])
    salida = prep.transform(["¿Cuánto cuesta la chaqueta de cuero, porfa?", "Hola, buenas tardes"])
    assert salida == ["cuanto costar chaqueta cuero", "hola buena tarde"]


def test_modo_stem():
    prep = TextPreprocessor(modo="stem").fit([])
    assert prep.transform(["¿tienen jeans negros?"]) == ["tien jeans negr"]


def test_stopwords_se_deciden_con_la_palabra_original():
    # "hay" se conserva aunque su lema sea "haber" (que sí es stop word)
    pasos = TextPreprocessor(modo="lema").pasos("¿hay poleras en talla m?")
    assert "hay" in pasos["sin_stopwords"]
    assert pasos["lemas_o_raices"][0] == "haber"


def test_pasos_contiene_todas_las_etapas():
    pasos = TextPreprocessor().pasos("¿Tienen JEANS en talla-32?")
    assert pasos["normalizado"] == "tienen jeans en talla-32"
    assert pasos["tokens"] == ["tienen", "jeans", "en", "talla", "32"]
    assert pasos["stopwords_eliminadas"] == ["en"]
    assert pasos["sin_stopwords"] == ["tienen", "jeans", "talla", "32"]
    assert pasos["final"] == pasos["lemas_o_raices"]


def test_extra_y_exclude():
    prep = TextPreprocessor(stopwords_extra=["quiero"], stopwords_exclude=["la"])
    assert prep.transform(["quiero la polera"]) == ["el polera"]


@pytest.mark.parametrize("valor", [None, 32, ""])
def test_entradas_no_validas_dan_texto_vacio(valor):
    assert TextPreprocessor().transform([valor]) == [""]


def test_parametros_invalidos():
    with pytest.raises(ValueError, match="modo"):
        TextPreprocessor(modo="otro").fit([])
    with pytest.raises(ValueError, match="lista_stopwords"):
        TextPreprocessor(lista_stopwords="otra").fit([])


def test_se_puede_clonar_para_gridsearch():
    prep = TextPreprocessor(modo="stem", stopwords_extra=["oye"])
    copia = clone(prep)
    assert copia.get_params() == prep.get_params()


def test_crear_preprocesador_desde_config():
    config = {"nlp": {"modo": "stem", "stopwords_extra": ["quiero"], "stopwords_exclude": None}}
    prep = crear_preprocesador(config)
    assert prep.modo == "stem"
    assert prep.stopwords_extra == ["quiero"]
    assert prep.stopwords_exclude == ()


def test_preprocesar_pasos_usa_config_del_proyecto():
    pasos = preprocesar_pasos("¿Cuánto cuesta la chaqueta, porfa?")
    assert pasos["final"] == ["cuanto", "costar", "chaqueta"]
