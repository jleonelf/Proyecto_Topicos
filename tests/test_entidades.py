"""Pruebas unitarias para el extractor de entidades (Fase Backend/NLP).

Responsable: Ramiro
"""

import pytest
from src.nlp.entidades import extraer_entidades


def test_extraccion_completa_consulta_stock():
    """Verifica que se detecten simultáneamente talla, color y prenda."""
    texto = "¿Tienen jeans negros en talla 32?"
    entidades = extraer_entidades(texto)

    assert entidades["talla"] == "32"
    assert entidades["color"] == "negro"
    assert entidades["producto"] == "jeans"
    assert entidades["categoria"] == "pantalones"
    assert entidades["fecha"] is None


def test_extraccion_tallas_alfabeticas():
    """Verifica detección de tallas alfabéticas y compuestas."""
    assert extraer_entidades("busco polera blanca en talla M")["talla"] == "M"
    assert extraer_entidades("les queda la chaqueta en talla XL")["talla"] == "XL"
    assert extraer_entidades("vestido floreado talla XS")["talla"] == "XS"
    assert extraer_entidades("prenda en talla S/M")["talla"] == "S/M"


def test_extraccion_tallas_numericas():
    """Verifica detección de tallas numéricas de pantalones y calzado."""
    assert extraer_entidades("pantalón talla 38")["talla"] == "38"
    assert extraer_entidades("jeans de vestir número 40")["talla"] == "40"


def test_extraccion_colores_con_variaciones():
    """Verifica que colores femeninos y plurales se normalicen a su forma canónica."""
    assert extraer_entidades("polera negra")["color"] == "negro"
    assert extraer_entidades("botines rojos")["color"] == "rojo"
    assert extraer_entidades("falda azul marino")["color"] == "azul"
    assert extraer_entidades("chamarra café")["color"] == "café"


def test_extraccion_productos_y_categorias_base():
    """Verifica mapeo de prendas típicas a sus categorías correspondientes."""
    ent_chaqueta = extraer_entidades("cuánto cuesta la chaqueta de cuero")
    assert ent_chaqueta["producto"] == "chaqueta"
    assert ent_chaqueta["categoria"] == "abrigos"

    ent_polera = extraer_entidades("tienen stock de polera")
    assert ent_polera["producto"] == "polera"
    assert ent_polera["categoria"] == "camisetas"


def test_extraccion_con_catalogo_personalizado():
    """Verifica que un catálogo importado de la tienda tenga prioridad."""
    catalogo_demo = {
        "productos": [
            {"nombre": "Polera Grunge Edición Especial", "categoria": "Colección Urbana"},
            {"nombre": "Botines Chelsea Cuero", "categoria": "Calzado Premium"},
        ]
    }
    entidades = extraer_entidades(
        "¿tienen stock de la polera grunge edición especial en negro?",
        catalogo=catalogo_demo,
    )
    assert entidades["producto"] == "Polera Grunge Edición Especial"
    assert entidades["categoria"] == "Colección Urbana"
    assert entidades["color"] == "negro"


def test_extraccion_fechas_administrativas():
    """Verifica detección de expresiones de tiempo para intenciones de admin."""
    assert extraer_entidades("dame el reporte de ventas de hoy")["fecha"] == "hoy"
    assert extraer_entidades("cuánto se vendió esta semana")["fecha"] == "esta semana"
    assert extraer_entidades("artículos más vendidos de octubre")["fecha"] == "octubre"
    assert extraer_entidades("balance del 2026-10-15")["fecha"] == "2026-10-15"


def test_consulta_sin_entidades():
    """Verifica que una consulta como saludo o despedida devuelva campos en None."""
    entidades = extraer_entidades("hola buenas tardes como estan")
    assert entidades["talla"] is None
    assert entidades["color"] is None
    assert entidades["producto"] is None
    assert entidades["categoria"] is None
    assert entidades["fecha"] is None
