"""Pruebas unitarias para el pipeline de entrenamiento e inferencia.

Responsable: Jorge.
"""

import os
import pytest
from src.models.train import entrenar, cargar_configuracion
from src.models.predict import predecir, cargar_modelo


def test_cargar_configuracion():
    """Verifica que el archivo de configuración exista y contenga claves requeridas."""
    config = cargar_configuracion()
    assert "models" in config
    assert "data" in config
    assert "inference" in config
    assert "artifacts" in config


def test_entrenar_y_generar_artefactos(tmp_path):
    """Verifica que el script de entrenamiento genere modelo.joblib y metricas.json."""
    pipeline, resultados = entrenar()
    assert pipeline is not None
    assert "modelos" in resultados
    assert "dummy_baseline" in resultados["modelos"]
    assert "naive_bayes" in resultados["modelos"]
    assert "regresion_logistica" in resultados["modelos"]
    assert "modelo_produccion" in resultados

    assert os.path.exists("artifacts/modelo.joblib")
    assert os.path.exists("artifacts/metricas.json")


def test_predecir_consulta_valida():
    """Verifica la respuesta de inferencia con una consulta típica."""
    res = predecir("¿tienen pantalones en talla 32?")
    assert "intencion" in res
    assert "probabilidad" in res
    assert "top3" in res
    assert "confianza_suficiente" in res
    assert isinstance(res["probabilidad"], float)
    assert len(res["top3"]) > 0


def test_predecir_texto_vacio():
    """Verifica que un texto vacío se maneje de forma segura sin excepciones."""
    res = predecir("")
    assert res["intencion"] == "desconocido"
    assert res["confianza_suficiente"] is False
    assert res["probabilidad"] == 0.0


def test_predecir_top3_ordenado():
    """Verifica que el top 3 de predicciones esté ordenado de mayor a menor probabilidad."""
    res = predecir("hola buenas tardes")
    top3 = res["top3"]
    assert len(top3) <= 3
    probs = [item["probabilidad"] for item in top3]
    assert probs == sorted(probs, reverse=True)
