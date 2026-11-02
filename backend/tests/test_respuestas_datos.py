"""Pruebas de las respuestas del chatbot con datos reales de la base.

Responsable: Fernando. Usan una base SQLite temporal, nunca la base real.
"""

import io

import pandas as pd
import pytest

from api.services.chat_service import generar_respuesta_chat
from api.services.respuestas_datos import responder_con_datos
from src.data import conexion
from src.data.inventario import catalogo_para_entidades, importar_tablas
from src.nlp.entidades import extraer_entidades

PRODUCTOS = """sku,nombre,categoria,talla,color,precio,stock
J-32-N,Jean Slim,pantalones,32,negro,250,3
J-34-N,Jean Slim,pantalones,34,negro,250,0
J-34-A,Jean Slim,pantalones,34,azul,240,6
P-M-B,Polera Básica,poleras,M,blanco,80,10
"""
VENTAS = """fecha,sku,cantidad,precio_unitario
2026-10-01,J-32-N,2,250
2026-10-02,P-M-B,5,80
"""
TIENDA = """nombre,direccion,horarios,envios,devoluciones,metodos_pago
Aura Boutique,Av. Ballivián 123,de lunes a sábado de 9:00 a 20:00,Enviamos a todo el país en 48 horas.,Cambios hasta 15 días con etiqueta.,"efectivo, tarjeta y QR"
"""


@pytest.fixture
def base_con_datos(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(conexion, "ruta_sqlite", lambda: tmp_path / "tienda.db")
    hojas = [(n, pd.read_csv(io.StringIO(c), dtype=str)) for n, c in
             [("tienda", TIENDA), ("ventas", VENTAS), ("productos", PRODUCTOS)]]
    importar_tablas(hojas)


def _entidades(texto):
    return extraer_entidades(texto, catalogo_para_entidades())


def test_stock_exacto(base_con_datos):
    r = responder_con_datos("consultar_stock", _entidades("¿tienen jeans negros en talla 32?"))
    assert r == "¡Sí! Tenemos disponible Jean Slim talla 32 negro: 3 unid. a Bs 250."


def test_stock_agotado_ofrece_alternativas(base_con_datos):
    r = responder_con_datos("consultar_stock", _entidades("¿hay jeans negros en talla 34?"))
    assert r.startswith("No nos queda")
    assert "32" in r and "azul" in r  # alternativas con stock


def test_producto_inexistente(base_con_datos):
    r = responder_con_datos("consultar_stock", _entidades("¿tienen vestidos rojos?"))
    assert r.startswith("No encontré") and "pantalones" in r and "poleras" in r


def test_precio_con_rango(base_con_datos):
    r = responder_con_datos("consultar_precio", _entidades("¿cuánto cuestan los jeans?"))
    assert r == "Estos son los precios: Jean Slim: de Bs 240 a Bs 250."


def test_tallas_disponibles_solo_con_stock(base_con_datos):
    r = responder_con_datos("consultar_tallas", _entidades("¿qué tallas hay de jeans?"))
    assert r == "Tallas disponibles ahora: Jean Slim: 32 y 34."


def test_datos_de_la_tienda(base_con_datos):
    assert "Aura Boutique" in responder_con_datos("saludo", {})
    assert responder_con_datos("envios", {}) == "Enviamos a todo el país en 48 horas."
    assert "Av. Ballivián 123" in responder_con_datos("horarios_ubicacion", {})
    assert responder_con_datos("metodos_pago", {}) == "Aceptamos: efectivo, tarjeta y QR."


def test_reportes_de_administracion(base_con_datos):
    assert "2 ventas" in responder_con_datos("reporte_ventas", {})
    assert responder_con_datos("productos_mas_vendidos", {}).startswith("Más vendidos del 2026-10-01 al 2026-10-02: 1. Polera Básica (5 unid.)")
    assert "Jean Slim talla 34 negro (0 unid.)" in responder_con_datos("stock_bajo", {})
    assert "poleras" in responder_con_datos("ventas_por_categoria", {})


def test_sin_base_usa_plantillas(tmp_path, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(conexion, "ruta_sqlite", lambda: tmp_path / "no_existe.db")
    assert responder_con_datos("consultar_stock", {"producto": "jeans"}) is None
    # El chat cae en la plantilla de Ramiro
    intencion, respuesta = generar_respuesta_chat("envios", 0.95, {})
    assert intencion == "envios" and "envíos" in respuesta


def test_chat_usa_datos_reales(base_con_datos):
    intencion, respuesta = generar_respuesta_chat("consultar_stock", 0.95, _entidades("¿tienen jeans negros en talla 32?"))
    assert "3 unid." in respuesta
