"""Pruebas unitarias para el detector de rechazo fuera de dominio (OOD).

Verifica de forma cuantitativa y reproducible las estrategias modulares de detección OOD:
- MSP (Maximum Softmax Probability)
- Margen entre Clases (Top1 - Top2)
- Similitud Coseno a Centroides
- Cobertura de Vocabulario
- Detector Híbrido Compuesto (Dual-Gate)

Responsable: Jorge (Fase 6).
"""

import os
from pathlib import Path
import pandas as pd
import pytest

from src.models.predict import cargar_modelo, resolver_ruta
from src.models.ood import (
    MSPDetector,
    MarginDetector,
    CosineCentroidDetector,
    VocabularyCoverageDetector,
    HybridOODDetector,
    comparar_estrategias
)


@pytest.fixture(scope="module")
def pipeline_entrenado():
    """Fixture que provee el pipeline serializado en producción."""
    return cargar_modelo()


def test_instanciacion_y_score_detectores(pipeline_entrenado):
    """Verifica que todos los detectores modulares se ajusten y computen scores continuos."""
    consultas = [
        "hola buenos días",
        "cuánto cuesta el vestido rojo",
        "cómo cambiar la contraseña del wifi"
    ]

    msp = MSPDetector(umbral=0.35).fit(pipeline_entrenado)
    margin = MarginDetector(umbral=0.20).fit(pipeline_entrenado)
    cov = VocabularyCoverageDetector(umbral=0.40).fit(pipeline_entrenado)
    hybrid = HybridOODDetector(umbral_prob=0.35, umbral_cobertura=0.35).fit(pipeline_entrenado)

    scores_msp = msp.score(consultas)
    assert len(scores_msp) == len(consultas)
    assert all(0.0 <= s <= 1.0 for s in scores_msp)

    scores_margin = margin.score(consultas)
    assert len(scores_margin) == len(consultas)
    assert all(0.0 <= s <= 1.0 for s in scores_margin)

    scores_cov = cov.score(consultas)
    assert len(scores_cov) == len(consultas)
    assert all(0.0 <= s <= 1.0 for s in scores_cov)

    scores_hybrid = hybrid.score(consultas)
    assert len(scores_hybrid) == len(consultas)
    assert all(0.0 <= s <= 1.0 for s in scores_hybrid)


def test_estrategia_hibrida_rechaza_bugs_reportados(pipeline_entrenado):
    """Verifica que la estrategia híbrida (Dual-Gate) rechace los 3 casos adversarios del bug report.

    1. 'cómo cambiar la contraseña del wifi' (activa 'cambiar' de devoluciones)
    2. 'tengo fiebre y dolor de cabeza' (activa 'tengo' de tallas/stock)
    3. '¿cuánto cuesta un pasaje de avión?' (activa 'cuánto cuesta' de consultar_precio)
    """
    consultas_bug = [
        "cómo cambiar la contraseña del wifi",
        "tengo fiebre y dolor de cabeza",
        "¿cuánto cuesta un pasaje de avión?"
    ]

    detector = HybridOODDetector(
        umbral_prob=0.40,
        umbral_cobertura=0.35,
        umbral_similitud=0.0,
        modo="conjuncion"
    ).fit(pipeline_entrenado)

    diagnosticos = detector.diagnosticar(consultas_bug)

    for diag in diagnosticos:
        assert diag["aceptada"] is False, (
            f"Consulta adversaria '{diag['texto']}' debió ser rechazada por el detector híbrido, "
            f"pero fue aceptada. Diagnóstico: {diag}"
        )
        assert diag["motivo_rechazo"] == "cobertura_baja", (
            f"Consulta '{diag['texto']}' debió ser rechazada por baja cobertura de vocabulario, "
            f"pero el motivo fue '{diag['motivo_rechazo']}'"
        )
        # La cobertura de tokens de la tienda de ropa debe ser baja (< 0.35)
        assert diag["cobertura"] < 0.35


def test_estrategia_hibrida_acepta_consultas_en_dominio(pipeline_entrenado):
    """Verifica que consultas legítimas en dominio mantengan alta cobertura y sean aceptadas."""
    consultas_id = [
        "hola muy buenas tardes",
        "¿cuánto cuesta este vestido de fiesta?",
        "¿tienen pantalones jeans en talla 32?",
        "¿hacen envíos a Cochabamba y Santa Cruz?",
        "muchas gracias hasta luego",
        "dame el reporte de ventas del día de hoy"
    ]

    detector = HybridOODDetector(
        umbral_prob=0.35,
        umbral_cobertura=0.33,
        umbral_similitud=0.0,
        modo="conjuncion"
    ).fit(pipeline_entrenado)

    aceptadas = detector.predict_accept(consultas_id)
    assert all(aceptadas), (
        f"Todas las consultas legítimas en dominio debieron ser aceptadas. Resultados: {aceptadas}"
    )


def test_evaluacion_y_comparacion_estrategias(pipeline_entrenado):
    """Verifica que comparar_estrategias() ejecute la grilla comparativa y devuelva métricas válidas."""
    # Muestra reducida para validación rápida en tests
    X_train = [
        "hola buenos días", "cuánto cuesta la falda", "tienen camisas talla l",
        "hacen envíos a domicilio", "hasta luego gracias"
    ]
    y_train = ["saludo", "consultar_precio", "consultar_tallas", "envios", "despedida"]

    X_val_id = [
        "buenas tardes", "precio de este vestido", "talla de pantalón", "costo de envío", "adiós nos vemos"
    ]
    y_val_id = ["saludo", "consultar_precio", "consultar_tallas", "envios", "despedida"]

    X_val_ood = [
        "cómo reparar la pantalla rota de la computadora",
        "receta de pastel de chocolate casero",
        "cuál es la distancia entre el sol y marte"
    ]

    res = comparar_estrategias(
        pipeline=pipeline_entrenado,
        X_train=X_train,
        y_train=y_train,
        X_val_id=X_val_id,
        y_val_id=y_val_id,
        X_val_ood=X_val_ood
    )

    assert "tabla_comparativa" in res
    assert "estrategia_seleccionada" in res
    assert "resumen_ganador" in res

    tabla = res["tabla_comparativa"]
    assert "msp_baseline_035" in tabla
    assert "hybrid_dual_gate" in tabla

    for nombre, metricas in tabla.items():
        assert "cobertura_id" in metricas
        assert "tasa_error_ood" in metricas
        assert "f1_macro" in metricas
        assert 0.0 <= metricas["tasa_error_ood"] <= 1.0


def test_sin_listas_negras_ni_reglas_ad_hoc():
    """Verifica que los detectores OOD utilicen propiedades estadísticas y no listas negras de palabras."""
    import inspect
    from src.models import ood

    codigo = inspect.getsource(ood)
    # Verificar que no existan listas negras de palabras
    assert "blacklist" not in codigo.lower()
    assert "palabras_prohibidas" not in codigo.lower()
    assert "wifi" not in codigo.lower()
    assert "fiebre" not in codigo.lower()
    assert "avion" not in codigo.lower()
    assert "avión" not in codigo.lower()
