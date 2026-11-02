"""Pruebas de las fases 1 (normalización) y 2 (tokenización). Responsable: Carmen."""

import pytest

from src.nlp.normalizacion import normalizar
from src.nlp.tokenizacion import tokenizar


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("HOLA Mundo", "hola mundo"),
        ("¿Qué canción?", "que cancion"),
        ("Pingüino", "pinguino"),
        ("Talla pequeña, año 2026", "talla pequeña año 2026"),
        ("mira https://tienda.com/jeans y www.ropa.bo", "mira y"),
        ("escribe a ventas@tienda.com o @aura_boutique", "escribe a o"),
        ("me encanta 😍🔥!!!", "me encanta"),
        ("jean's", "jeans"),
        ("cuesta 12.50 o 12,50", "cuesta 12.50 o 12.50"),
        ("talla S/M", "talla s/m"),
        ("Talla-M", "talla-m"),
        ("  muchos    espacios  ", "muchos espacios"),
        ("", ""),
    ],
)
def test_normalizar(entrada, esperado):
    assert normalizar(entrada) == esperado


def test_normalizar_conserva_tallas_numericas():
    assert "32" in normalizar("¿Tienen jeans en talla 32?")


@pytest.mark.parametrize("entrada", [None, 123, ["texto"]])
def test_normalizar_entrada_no_texto(entrada):
    assert normalizar(entrada) == ""


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("talla-m", ["talla", "m"]),
        ("xl", ["xl"]),
        ("s/m", ["s/m"]),
        ("100bs", ["100", "bs"]),
        ("jeans", ["jeans"]),
        ("precio 12.50", ["precio", "12.50"]),
        ("", []),
    ],
)
def test_tokenizar_casos_del_dominio(entrada, esperado):
    assert tokenizar(entrada) == esperado


def test_tokenizar_entrada_no_texto():
    assert tokenizar(None) == []


def test_fases_1_y_2_encadenadas():
    texto = "¿Tienen JEAN'S en Talla-M a 100Bs? 😍 https://aura.bo"
    assert tokenizar(normalizar(texto)) == ["tienen", "jeans", "en", "talla", "m", "a", "100", "bs"]
