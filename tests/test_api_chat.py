"""Pruebas automatizadas para los endpoints /predict y /chat (feat/api-chat).

Responsable: Ramiro (Backend)
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """Cliente de pruebas para la API."""
    return TestClient(app)


def test_predict_exitoso(client):
    """Verifica que /predict retorne intención, probabilidad y top 3."""
    payload = {"texto": "¿Tienen jeans negros en talla 32?"}
    response = client.post("/predict", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "intencion" in data
    assert "probabilidad" in data
    assert "top3" in data
    assert isinstance(data["top3"], list)
    assert len(data["top3"]) == 3
    assert data["probabilidad"] > 0.0


def test_predict_validacion_texto_invalido(client):
    """Verifica que /predict rechace textos inválidos con error 422."""
    response = client.post("/predict", json={"texto": "  "})
    assert response.status_code == 422
    assert "Error de validación" in response.json()["error"]


def test_chat_consulta_stock_cliente(client):
    """Verifica flujo completo de /chat para consulta de stock con entidades."""
    payload = {
        "texto": "¿Tienen stock de polera blanca en talla M?",
        "rol": "cliente",
    }
    response = client.post("/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["intencion"] == "consultar_stock"
    assert data["probabilidad"] >= 0.60
    assert data["entidades"]["talla"] == "M"
    assert data["entidades"]["color"] == "blanco"
    assert data["entidades"]["producto"] == "polera"
    assert "blanca" in data["respuesta"] or "blanco" in data["respuesta"]
    assert "M" in data["respuesta"]

    # Verificar que devuelva los pasos para el frontend
    pasos = data["pasos"]
    assert pasos is not None
    assert "normalizado" in pasos
    assert "tokens" in pasos
    assert "sin_stopwords" in pasos
    assert "lemas_o_raices" in pasos


def test_chat_consulta_admin_con_fechas(client):
    """Verifica que el rol admin maneje intenciones de reporte con fecha."""
    payload = {
        "texto": "Dame el reporte de ventas de esta semana",
        "rol": "admin",
    }
    response = client.post("/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["intencion"] == "reporte_ventas"
    assert data["entidades"]["fecha"] == "esta semana"
    assert "Reporte administrativo" in data["respuesta"]


def test_chat_umbral_confianza_frase_ambigua(client):
    """Verifica que una frase incomprensible caiga por debajo del umbral de confianza (< 0.60)."""
    payload = {
        "texto": "abcdef qwerty zzz ppp jjj",
        "rol": "cliente",
    }
    response = client.post("/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    # Si la probabilidad es menor que el umbral (0.60), la intención es desconocida
    assert data["intencion"] == "desconocido"
    assert data["probabilidad"] < 0.60
    assert "No estoy seguro de haber entendido" in data["respuesta"]


def test_chat_validacion_rol_invalido(client):
    """Verifica que rechace roles no autorizados."""
    payload = {
        "texto": "Hola buenas tardes",
        "rol": "gerente_general",  # Solo se permite 'cliente' o 'admin'
    }
    response = client.post("/chat", json=payload)
    assert response.status_code == 422
