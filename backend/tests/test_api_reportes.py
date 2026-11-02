"""Pruebas automatizadas para los endpoints de métricas, reportes y predicción en lote.

Responsable: Ramiro (Backend)
"""

import io
import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    """Cliente de pruebas para interactuar con la API."""
    return TestClient(app)


def test_get_metrics(client):
    """Verifica que /metrics retorne las métricas del modelo y la matriz de confusión."""
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()

    assert "modelo_activo" in data
    assert "accuracy" in data
    assert "f1_macro" in data
    assert "f1_por_clase" in data
    assert "matriz_confusion" in data
    assert data["accuracy"] > 0.80
    assert data["f1_macro"] > 0.80


@pytest.mark.parametrize("tipo", ["ventas", "mas_vendidos", "stock_bajo", "categorias"])
def test_get_reportes_tipos_validos(client, tipo):
    """Verifica que los 4 tipos de reportes administrativos respondan con datos estructurados."""
    response = client.get(f"/reportes/{tipo}")
    assert response.status_code == 200
    data = response.json()

    assert data["tipo_reporte"] == tipo
    assert "resumen" in data
    assert "datos" in data
    assert isinstance(data["datos"], list)


def test_get_reportes_tipo_invalido(client):
    """Verifica que un tipo de reporte desconocido devuelva error 400 con mensaje claro."""
    response = client.get("/reportes/tipo_inventado")
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "Tipo de reporte inválido" in data["error"]


def test_predict_lote_json(client):
    """Verifica predicción masiva enviando un arreglo JSON de frases."""
    payload = {
        "textos": [
            "¿Tienen jeans en talla 32?",
            "¿Cuánto cuesta la chaqueta de cuero?",
            "Horarios de atención de la tienda",
        ]
    }
    response = client.post("/predict/lote", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 3
    assert len(data["predicciones"]) == 3
    for pred in data["predicciones"]:
        assert "texto" in pred
        assert "intencion" in pred
        assert "probabilidad" in pred


def test_predict_lote_json_vacio(client):
    """Verifica que una lista vacía de textos sea rechazada con 422."""
    response = client.post("/predict/lote", json={"textos": []})
    assert response.status_code == 422


def test_predict_lote_archivo_txt(client):
    """Verifica procesamiento de archivo de texto con una frase por línea."""
    contenido = "¿Tienen stock de polera?\n¿Cuánto vale el vestido?\n"
    archivo_mock = ("consultas.txt", io.BytesIO(contenido.encode("utf-8")), "text/plain")

    response = client.post(
        "/predict/lote/archivo",
        files={"archivo": archivo_mock},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["predicciones"]) == 2


def test_predict_lote_archivo_formato_incorrecto(client):
    """Verifica que un archivo con extensión no permitida (ej. .pdf) devuelva error 400."""
    archivo_pdf = ("consultas.pdf", io.BytesIO(b"%PDF-1.4..."), "application/pdf")
    response = client.post(
        "/predict/lote/archivo",
        files={"archivo": archivo_pdf},
    )
    assert response.status_code == 400
    assert "Formato de archivo inválido" in response.json()["error"]


def test_tienda_importar_exitoso(client):
    """Verifica que la subida de un archivo CSV de tienda responda exitosamente."""
    contenido_csv = "sku,nombre,categoria,talla,color,precio,stock\n1,Jeans,pantalones,32,negro,120,10\n"
    archivo_csv = ("productos.csv", io.BytesIO(contenido_csv.encode("utf-8")), "text/csv")

    response = client.post(
        "/tienda/importar",
        files={"archivo": archivo_csv},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["estado"] == "exitoso"
    assert "productos_importados" in data
    assert "ventas_importadas" in data


def test_tienda_importar_formato_incorrecto(client):
    """Verifica que formatos no válidos para la tienda sean rechazados con 400."""
    archivo_invalido = ("datos.docx", io.BytesIO(b"fake word doc"), "application/octet-stream")
    response = client.post(
        "/tienda/importar",
        files={"archivo": archivo_invalido},
    )
    assert response.status_code == 400
    assert "Formato de archivo incorrecto" in response.json()["error"]
