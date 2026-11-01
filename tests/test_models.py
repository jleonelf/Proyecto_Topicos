"""Pruebas unitarias y de integración para el pipeline de entrenamiento e inferencia.

Responsable: Jorge (Fase 6).
"""

import os
from pathlib import Path
import pytest
from src.models.train import entrenar, cargar_configuracion
from src.models.predict import predecir, cargar_modelo, cargar_detector, invalidar_cache, resolver_ruta


def test_cargar_configuracion():
    """Verifica que el archivo de configuración exista y contenga claves requeridas."""
    config = cargar_configuracion()
    assert "models" in config
    assert "data" in config
    assert "inference" in config
    assert "artifacts" in config
    assert "umbral" in config["inference"]
    assert config["inference"]["umbral"] > 0.0


def test_entrenar_y_generar_artefactos(tmp_path):
    """Verifica que el script de entrenamiento genere modelo.joblib y metricas.json con selección por CV."""
    pipeline, resultados = entrenar()
    assert pipeline is not None
    assert "modelos" in resultados
    assert "dummy_baseline" in resultados["modelos"]
    assert "naive_bayes" in resultados["modelos"]
    assert "regresion_logistica" in resultados["modelos"]
    assert "modelo_produccion" in resultados

    prod = resultados["modelo_produccion"]
    assert "criterio" in prod
    assert "validación cruzada" in prod["criterio"].lower()
    assert "mejor_cv_score" in prod
    assert prod["mejor_cv_score"] > 0.70

    assert os.path.exists("artifacts/modelo.joblib")
    assert os.path.exists("artifacts/metricas.json")
    ood = resultados["estrategias_rechazo_ood"]
    assert ood["evaluacion_final_test"]["n_ood_test"] == 50
    assert 0 <= ood["evaluacion_final_test"]["tasa_error_ood"] <= 1


def test_predecir_contrato_estricto():
    """Verifica el contrato estricto de retorno de la función predecir(texto)."""
    res = predecir("¿tienen pantalones en talla 32?")
    # Claves obligatorias según especificación
    claves_esperadas = {
        "texto",
        "intencion",
        "intencion_detectada",
        "probabilidad",
        "top3",
        "umbral",
        "confianza_suficiente"
    }
    for clave in claves_esperadas:
        assert clave in res, f"Falta la clave requerida '{clave}' en la salida de predecir()"

    assert isinstance(res["texto"], str)
    assert isinstance(res["intencion"], str)
    assert isinstance(res["intencion_detectada"], str)
    assert isinstance(res["probabilidad"], float)
    assert isinstance(res["umbral"], float)
    assert isinstance(res["confianza_suficiente"], bool)
    assert isinstance(res["top3"], list)
    assert len(res["top3"]) > 0

    for item in res["top3"]:
        assert "intencion" in item
        assert "probabilidad" in item
        assert isinstance(item["probabilidad"], float)


def test_predecir_consultas_en_dominio_validas():
    """Verifica que consultas típicas en dominio superen el umbral y devuelvan su intención correcta."""
    consultas_en_dominio = [
        ("hola buenas tardes", "saludo"),
        ("muchas gracias hasta luego", "despedida"),
        ("¿cuánto cuesta este vestido de fiesta?", "consultar_precio"),
        ("¿hacen envíos a Cochabamba y Santa Cruz?", "envios"),
        ("¿en qué dirección se encuentra la tienda física?", "horarios_ubicacion"),
        ("dame el reporte de ventas del día de hoy", "reporte_ventas"),
        ("¿cuáles son los productos más vendidos del mes?", "productos_mas_vendidos"),
        ("¿qué prendas tienen stock bajo en inventario?", "stock_bajo"),
        ("ventas por categoria del mes", "ventas_por_categoria"),
    ]

    for texto, intencion_esperada in consultas_en_dominio:
        res = predecir(texto)
        assert res["confianza_suficiente"] is True, (
            f"Consulta en dominio '{texto}' debió superar el umbral ({res['umbral']}), pero obtuvo prob={res['probabilidad']}"
        )
        assert res["intencion"] == intencion_esperada, (
            f"Consulta '{texto}' esperaba intención '{intencion_esperada}', se obtuvo '{res['intencion']}'"
        )
        assert res["intencion"] != "no_entendido"


def test_predecir_consultas_ood_no_vistas_rechazadas():
    """Verifica que consultas OOD del conjunto de prueba independiente (ood_test.csv) sean rechazadas."""
    # Consultas no utilizadas para escoger el umbral, pertenecientes al test set OOD
    consultas_ood_test = [
        "quiero reparar la pantalla quebrada de mi laptop",
        "dónde venden entradas populares para el concierto de rock",
        "cuál es el vehículo más vendido en el mercado nacional este año",
        "cuál es la capital administrativa de la república de sudáfrica",
        "cómo detectar fugas de agua subterráneas en el jardín",
        "cuál es la diferencia entre rocas ígneas y sedimentarias en geología",
        "cuántos satélites naturales conocidos orbitan alrededor del planeta júpiter",
        "un zapato volador en la luna",
        "receta de tarta de manzana con canela"
    ]

    for texto in consultas_ood_test:
        res = predecir(texto)
        assert res["confianza_suficiente"] is False, (
            f"Consulta OOD '{texto}' no debió superar el umbral ({res['umbral']}), obtuvo prob={res['probabilidad']}"
        )
        assert res["intencion"] == "no_entendido", (
            f"Consulta OOD '{texto}' debió clasificarse como 'no_entendido', se obtuvo '{res['intencion']}'"
        )


def test_predecir_frases_del_bug_rechazadas():
    """Verifica que las 3 frases reportadas en el bug de sobreconfianza OOD sean rechazadas como no_entendido."""
    frases_bug = [
        "cómo cambiar la contraseña del wifi",
        "tengo fiebre y dolor de cabeza",
        "¿cuánto cuesta un pasaje de avión?"
    ]
    for texto in frases_bug:
        res = predecir(texto)
        assert res["confianza_suficiente"] is False, (
            f"Frase del bug '{texto}' debió ser rechazada por el detector OOD, pero obtuvo confianza_suficiente=True"
        )
        assert res["intencion"] == "no_entendido", (
            f"Frase del bug '{texto}' debió tener intención 'no_entendido', se obtuvo '{res['intencion']}'"
        )


def test_predecir_texto_vacio_y_espacios():
    """Verifica que entradas vacías o compuestas sólo de espacios se manejen con seguridad sin excepciones."""
    casos_vacios = ["", "   ", "\t\n  "]
    for caso in casos_vacios:
        res = predecir(caso)
        assert res["intencion"] == "desconocido"
        assert res["intencion_detectada"] == "desconocido"
        assert res["confianza_suficiente"] is False
        assert res["probabilidad"] == 0.0
        assert res["top3"] == []


def test_predecir_top3_ordenado():
    """Verifica que el top 3 de predicciones esté ordenado descendentemente por probabilidad."""
    res = predecir("hola buenas tardes")
    top3 = res["top3"]
    assert len(top3) <= 3
    probs = [item["probabilidad"] for item in top3]
    assert probs == sorted(probs, reverse=True)


def test_rutas_relativas_y_absolutas(tmp_path):
    """Verifica que cargar_modelo() y predecir() funcionen con rutas relativas, absolutas o desde otro directorio."""
    invalidar_cache()

    # 1. Ruta relativa por defecto
    m1 = cargar_modelo()
    assert m1 is not None

    # 2. Ruta absoluta explícita
    ruta_abs = resolver_ruta("artifacts/modelo.joblib")
    invalidar_cache()
    m2 = cargar_modelo(ruta_abs)
    assert m2 is not None

    # 3. Ejecución cambiando el directorio actual de trabajo
    cwd_original = os.getcwd()
    try:
        os.chdir(tmp_path)
        invalidar_cache()
        # predecir() debe resolver correctamente artifacts/modelo.joblib hacia REPO_ROOT
        res = predecir("hola buenas tardes")
        assert res["intencion"] == "saludo"
        assert res["confianza_suficiente"] is True
    finally:
        os.chdir(cwd_original)
        invalidar_cache()


def test_regeneracion_desde_cero():
    """Verifica que si se invalida la caché o se recarga el modelo, funcione limpiamente sin modelos antiguos."""
    invalidar_cache()
    # Primera carga
    m1 = cargar_modelo()
    assert m1 is not None

    # Invalidar caché en memoria
    invalidar_cache()

    # Recargar tras invalidación
    m2 = cargar_modelo()
    assert m2 is not None

    res = predecir("¿hacen envíos a domicilio?")
    assert res["intencion"] == "envios"
    assert res["confianza_suficiente"] is True


def test_lematizacion_error_si_falta_spacy(monkeypatch):
    """Verifica que lematizar lance RuntimeError si spaCy no está disponible."""
    from src.nlp import lematizacion
    monkeypatch.setattr(lematizacion, "_get_spacy", lambda: False)
    lematizacion._lematizar_cached.cache_clear()

    with pytest.raises(RuntimeError, match="es_core_news_sm"):
        lematizacion.lematizar(["probando", "tokens"])


def test_detector_faltante_o_roto_no_acepta_consultas(monkeypatch, tmp_path):
    """Un fallo del detector no puede reactivar el umbral MSP inseguro."""
    import src.models.predict as modulo_predict

    invalidar_cache()
    with pytest.raises(FileNotFoundError, match="python -m src.models.train"):
        cargar_detector(str(tmp_path / "detector_inexistente.joblib"))

    class DetectorRoto:
        def predict_accept(self, textos):
            raise RuntimeError("fallo simulado")

    monkeypatch.setattr(modulo_predict, "cargar_detector", lambda: DetectorRoto())
    with pytest.raises(RuntimeError, match="Falló la evaluación del detector OOD"):
        predecir("cómo cambiar la contraseña del wifi")
    invalidar_cache()
