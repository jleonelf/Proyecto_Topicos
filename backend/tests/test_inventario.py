"""Pruebas del apartado "Inventarios y métricas": importación, analíticas y experimento.

Responsable: Fernando. Usan una base SQLite temporal, nunca la base real.
"""

import io

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.main import app
from src.data import conexion

PRODUCTOS_CSV = (
    "sku,nombre,categoria,talla,color,precio,stock\n"
    "J-32-N,Jean Slim,pantalones,32,negro,250,3\n"
    "J-34-N,Jean Slim,pantalones,34,negro,250,12\n"
    "P-M-B,Polera Básica,poleras,m,blanco,\"80,50\",2\n"
    "X-1,,poleras,m,rojo,90,4\n"  # sin nombre -> se omite
)

VENTAS_CSV = (
    "fecha,sku,cantidad,precio_unitario\n"
    "2026-10-01,J-32-N,2,250\n"
    "2026-10-01,P-M-B,5,80.5\n"
    "2026-10-02,J-34-N,1,240\n"
    "2026-10-02,NO-EXISTE,1,100\n"  # sku inexistente -> se omite
    "ayer,J-32-N,1,250\n"  # fecha inválida -> se omite
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    """API con una base SQLite vacía en una carpeta temporal."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(conexion, "ruta_sqlite", lambda: tmp_path / "tienda_test.db")
    return TestClient(app)


def _subir(client, nombre, contenido, tipo="text/csv", **params):
    return client.post("/inventario/importar", params=params,
                       files={"archivo": (nombre, io.BytesIO(contenido), tipo)})


def test_resumen_sin_base(client):
    assert client.get("/inventario/resumen").json()["disponible"] is False


def test_importar_productos_y_ventas_csv(client):
    r = _subir(client, "productos.csv", PRODUCTOS_CSV.encode())
    assert r.status_code == 200
    hoja = r.json()["hojas"][0]
    assert (hoja["tipo"], hoja["filas_importadas"], hoja["filas_omitidas"]) == ("productos", 3, 1)
    assert hoja["errores"][0]["fila"] == 5  # fila 1 = encabezado

    r = _subir(client, "ventas.csv", VENTAS_CSV.encode())
    hoja = r.json()["hojas"][0]
    assert (hoja["tipo"], hoja["filas_importadas"], hoja["filas_omitidas"]) == ("ventas", 3, 2)

    resumen = r.json()["inventario"]
    assert resumen["indicadores"]["productos"] == 3
    assert resumen["indicadores"]["transacciones"] == 3
    assert resumen["indicadores"]["ingresos"] == pytest.approx(2 * 250 + 5 * 80.5 + 240)
    assert resumen["mas_vendidos"][0]["nombre"] == "Polera Básica"  # 5 unidades
    assert [p["sku"] for p in resumen["stock_bajo"]] == ["P-M-B", "J-32-N"]  # stock <= 5


def test_reimportar_actualiza_productos_sin_duplicar(client):
    _subir(client, "productos.csv", PRODUCTOS_CSV.encode())
    _subir(client, "productos.csv", PRODUCTOS_CSV.replace(",250,3", ",260,30").encode())
    resumen = client.get("/inventario/resumen").json()
    assert resumen["indicadores"]["productos"] == 3
    assert "J-32-N" not in [p["sku"] for p in resumen["stock_bajo"]]  # ahora tiene 30


def test_excel_con_dos_hojas(client):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as escritor:
        pd.read_csv(io.StringIO(VENTAS_CSV)).to_excel(escritor, sheet_name="ventas", index=False)
        pd.read_csv(io.StringIO(PRODUCTOS_CSV)).to_excel(escritor, sheet_name="productos", index=False)
    r = _subir(client, "tienda.xlsx", buffer.getvalue(),
               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    assert r.status_code == 200
    # Los productos se importan primero aunque la hoja de ventas esté antes
    assert [h["tipo"] for h in r.json()["hojas"]] == ["productos", "ventas"]
    assert r.json()["inventario"]["indicadores"]["transacciones"] == 3


@pytest.mark.parametrize("nombre, contenido, detalle", [
    ("datos.pdf", b"%PDF", "Formato no soportado"),
    ("vacio.csv", b"", "vacío"),
    ("raro.csv", b"a,b\n1,2\n", "No se reconocen las columnas"),
])
def test_archivos_invalidos(client, nombre, contenido, detalle):
    r = _subir(client, nombre, contenido)
    assert r.status_code == 400
    assert detalle in r.json()["detalle"]


def test_frases_insuficientes_para_experimento(client):
    r = _subir(client, "frases.csv", "texto,intencion\nhola,saludo\nchau,despedida\n".encode())
    assert r.status_code == 422
    assert "al menos" in r.json()["detalle"]


def test_experimento_entrena_con_frases_etiquetadas(client, tmp_path, monkeypatch):
    from src.models import experimento
    monkeypatch.setattr(experimento, "RUTA_EXPERIMENTO", tmp_path / "experimento.json")

    frases = {
        "saludo": ["hola", "buenas tardes", "buenos dias", "hola que tal", "buenas noches",
                   "hola buen dia", "que tal buenas", "hola a todos", "saludos", "buenas"],
        "consultar_precio": ["cuanto cuesta el jean", "precio de la polera", "cuanto vale la chaqueta",
                             "que precio tiene", "cuanto sale el vestido", "valor del abrigo",
                             "cuanto cuesta esto", "precio del blazer", "cuanto es", "a cuanto esta"],
        "envios": ["hacen envios", "envian a provincia", "costo de envio", "cuanto tarda el envio",
                   "envios a domicilio", "mandan a cochabamba", "tienen delivery", "envio gratis",
                   "hacen entregas", "como envian"],
    }
    csv = "texto,intencion\n" + "".join(f"{t},{i}\n" for i, ts in frases.items() for t in ts)
    r = _subir(client, "frases.csv", csv.encode())
    assert r.status_code == 200
    resultado = r.json()["experimento"]
    assert resultado["frases"] == 30
    assert resultado["clases"] == ["consultar_precio", "envios", "saludo"]
    assert 0 <= resultado["experimento"]["f1_macro"] <= 1
    assert len(resultado["experimento"]["matriz_confusion"]) == 3
    # Queda guardado para recargar la vista
    assert TestClient(app).get("/metricas/experimento").json()["frases"] == 30


def test_metricas_entrenamiento_lee_metricas_json():
    datos = TestClient(app).get("/metricas/entrenamiento").json()
    assert datos["disponible"] is True
    assert {m["clave"] for m in datos["modelos"]} == {"dummy_baseline", "naive_bayes", "regresion_logistica"}
    produccion = next(m for m in datos["modelos"] if m["en_produccion"])
    assert len(produccion["matriz_confusion"]) == len(datos["clases"])
