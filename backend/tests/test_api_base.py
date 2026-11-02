"""Pruebas automatizadas para los endpoints base y esquemas de validación de la API.

Responsable: Ramiro (Backend)
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from api.main import app
from api.schemas import ConsultaTextoRequest, ChatRequest


@pytest.fixture
def client():
    """Cliente de pruebas para interactuar con la aplicación FastAPI."""
    return TestClient(app)


def test_endpoint_root(client):
    """Verifica que el endpoint raíz responda correctamente con metadatos."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "mensaje" in data
    assert "documentacion" in data
    assert "salud" in data
    assert data["documentacion"] == "/docs"


def test_endpoint_health(client):
    """Verifica que el endpoint /health informe el estado y los artefactos sin fallar."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["estado"] == "activo"
    assert "version" in data
    assert "modelo_cargado" in data
    assert "tienda_cargada" in data
    assert isinstance(data["detalles"], dict)


def test_endpoint_docs(client):
    """Verifica que la documentación interactiva Swagger (/docs) esté accesible."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_schema_consulta_texto_valido():
    """Verifica que un texto con longitud adecuada sea aceptado."""
    req = ConsultaTextoRequest(texto="¿Tienen jeans negros en talla 32?")
    assert req.texto == "¿Tienen jeans negros en talla 32?"


@pytest.mark.parametrize(
    "texto_invalido",
    [
        "",             # Vacío
        "   ",          # Solo espacios
        "ab",           # Menos de 3 caracteres
        "  a  ",        # Menos de 3 caracteres tras strip
        "x" * 501,      # Más de 500 caracteres
    ],
)
def test_schema_consulta_texto_invalido(texto_invalido):
    """Verifica que entradas vacías, muy cortas o excesivamente largas sean rechazadas."""
    with pytest.raises(ValidationError):
        ConsultaTextoRequest(texto=texto_invalido)


def test_schema_chat_roles_permitidos():
    """Verifica que ChatRequest acepte roles válidos ('cliente' y 'admin') y rechace otros."""
    req_cliente = ChatRequest(texto="Hola, buenos días", rol="cliente")
    assert req_cliente.rol == "cliente"

    req_admin = ChatRequest(texto="Reporte de ventas de hoy", rol="admin")
    assert req_admin.rol == "admin"

    with pytest.raises(ValidationError):
        ChatRequest(texto="Consulta de prueba", rol="superusuario")  # Rol no permitido
