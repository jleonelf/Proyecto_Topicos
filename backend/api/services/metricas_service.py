"""Métricas del entrenamiento preparadas para el apartado "Inventarios y métricas".

Responsable: Fernando.

Lee artifacts/metricas.json (lo genera train.py de Jorge) sin cambiar su formato
y lo reorganiza en la forma que necesita el frontend: un registro por modelo con
sus métricas de prueba, métricas por clase y matriz de confusión. Si el modelo
entrenado existe, agrega los términos que más empujan hacia cada intención.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

import joblib
import numpy as np

from src.config import config

RAIZ_BACKEND = Path(__file__).resolve().parent.parent.parent

# Nombres legibles de cada modelo de train.py
NOMBRES_MODELOS = {
    "dummy_baseline": "Línea base (clase más frecuente)",
    "naive_bayes": "Naive Bayes (ComplementNB)",
    "regresion_logistica": "Regresión logística",
}

# Claves del classification_report de scikit-learn que no son intenciones
_CLAVES_RESUMEN = {"accuracy", "macro avg", "weighted avg"}


def _ruta(clave: str, por_defecto: str) -> Path:
    """Ruta de un artefacto según la sección artifacts de config.yaml."""
    return RAIZ_BACKEND / config.get("artifacts", {}).get(clave, por_defecto)


def _por_clase(reporte: Dict[str, Any], clases: List[str]) -> Dict[str, Dict[str, float]]:
    """Precisión, recall, F1 y soporte de cada intención desde el classification_report."""
    resultado = {}
    for clase in clases:
        fila = reporte.get(clase)
        if not fila:
            continue
        resultado[clase] = {
            "precision": round(fila.get("precision", 0.0), 4),
            "recall": round(fila.get("recall", 0.0), 4),
            "f1": round(fila.get("f1-score", 0.0), 4),
            "soporte": int(fila.get("support", 0)),
        }
    return resultado


def _terminos_influyentes(n: int = 8) -> Dict[str, List[List[Any]]]:
    """Términos con mayor peso hacia cada intención en el modelo de producción.

    Solo aplica a modelos lineales (regresión logística o Naive Bayes), que
    tienen un peso por término y por clase.
    """
    ruta = _ruta("model_path", "artifacts/modelo.joblib")
    if not ruta.is_file():
        return {}
    try:
        pipeline = joblib.load(ruta)
        vectorizador = pipeline.named_steps["vectorizador"]
        modelo = pipeline.named_steps["modelo"]
        # coef_: regresión logística; feature_log_prob_: Naive Bayes
        pesos = getattr(modelo, "coef_", None)
        if pesos is None:
            pesos = getattr(modelo, "feature_log_prob_", None)
        if pesos is None:
            return {}
        terminos = np.array(vectorizador.get_feature_names_out())
        resultado = {}
        for i, clase in enumerate(modelo.classes_):
            mejores = np.argsort(pesos[i])[::-1][:n]  # índices de los n pesos más altos
            resultado[str(clase)] = [[str(terminos[j]), round(float(pesos[i][j]), 3)] for j in mejores]
        return resultado
    except Exception:
        return {}


def metricas_entrenamiento() -> Dict[str, Any]:
    """Métricas del último entrenamiento oficial, listas para el frontend."""
    ruta = _ruta("metrics_path", "artifacts/metricas.json")
    if not ruta.is_file():
        return {"disponible": False, "motivo": "Todavía no hay métricas. Ejecuta: python -m src.models.train"}

    datos = json.loads(ruta.read_text(encoding="utf-8"))
    clases = datos.get("clases", [])
    produccion = datos.get("modelo_produccion", {})

    modelos = []
    for clave, info in datos.get("modelos", {}).items():
        metricas = info.get("metricas", {})
        modelos.append({
            "clave": clave,
            "nombre": NOMBRES_MODELOS.get(clave, clave),
            "descripcion": info.get("descripcion", ""),
            "en_produccion": clave == produccion.get("nombre"),
            # La línea base no pasa por validación cruzada (train.py no la calcula)
            "cv_f1_macro": info.get("mejor_cv_score") if clave != "dummy_baseline" else None,
            "parametros": info.get("mejores_parametros", {}),
            "accuracy": metricas.get("accuracy"),
            "f1_macro": metricas.get("f1_macro"),
            "f1_weighted": metricas.get("f1_weighted"),
            "por_clase": _por_clase(metricas.get("classification_report", {}), clases),
            "matriz_confusion": metricas.get("confusion_matrix", []),
        })

    ood = datos.get("estrategias_rechazo_ood", {})
    configuracion = datos.get("configuracion", {})
    return {
        "disponible": True,
        "fecha": datos.get("fecha_entrenamiento"),
        "total_muestras": datos.get("total_muestras"),
        "muestras_train": datos.get("muestras_train"),
        "muestras_test": datos.get("muestras_test"),
        "clases": clases,
        "produccion": {
            "clave": produccion.get("nombre"),
            "nombre": NOMBRES_MODELOS.get(produccion.get("nombre"), produccion.get("nombre")),
            "criterio": produccion.get("criterio"),
            "cv_f1_macro": produccion.get("mejor_cv_score"),
            "test_f1_macro": produccion.get("test_f1_macro"),
            "test_accuracy": produccion.get("test_accuracy"),
        },
        "modelos": modelos,
        "ood": {
            "estrategia": ood.get("estrategia_seleccionada"),
            "criterio": ood.get("criterio_seleccion"),
            "evaluacion_test": ood.get("evaluacion_final_test", {}),
        },
        "configuracion": {
            "nlp": configuracion.get("nlp", {}),
            "vectorizador": configuracion.get("vectorizador") or configuracion.get("vectorizer", {}),
        },
        "terminos_influyentes": _terminos_influyentes(),
    }
