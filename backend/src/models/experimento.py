"""Entrenamiento experimental con un archivo de frases etiquetadas.

Responsable: Fernando (apartado "Inventarios y métricas").

Cuando el usuario sube un CSV/Excel con columnas texto + intencion, se entrena
un modelo APARTE con esas frases y se muestran sus métricas junto a las del
modelo oficial. El modelo del chat (artifacts/modelo.joblib) no se modifica.

El experimento usa exactamente el mismo pipeline que producción (fases 1 a 6,
configuradas desde src/config.yaml) y, si existe, los mejores hiperparámetros
que encontró train.py para la regresión logística. Así la comparación mide el
efecto de los DATOS y no de otra configuración.

Evaluación: división estratificada 80/20 del archivo. Además se mide cómo le va
al modelo oficial con esas mismas frases de prueba.
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline

from src.config import config
from src.nlp.pipeline import crear_preprocesador
from src.nlp.vectorizacion import crear_vectorizador

RAIZ_BACKEND = Path(__file__).resolve().parent.parent.parent
RUTA_EXPERIMENTO = RAIZ_BACKEND / "artifacts" / "experimento.json"  # último experimento, para recargar la vista

MIN_FRASES = 20  # con menos no hay suficiente para entrenar y probar
MIN_POR_CLASE = 2  # la división estratificada necesita al menos 2 por intención


class DatosInsuficientes(ValueError):
    """El archivo no tiene frases suficientes para entrenar (la API responde 422)."""


def _parametros_produccion() -> Dict[str, Any]:
    """Mejores hiperparámetros de la regresión logística según el último train.py."""
    rel = config.get("artifacts", {}).get("metrics_path", "artifacts/metricas.json")
    try:
        metricas = json.loads((RAIZ_BACKEND / rel).read_text(encoding="utf-8"))
        mejores = metricas["modelos"]["regresion_logistica"]["mejores_parametros"]
        return {
            "C": float(mejores.get("modelo__C", 1.0)),
            # train.py guarda None como el texto "None"
            "class_weight": None if mejores.get("modelo__class_weight") in (None, "None") else mejores["modelo__class_weight"],
        }
    except Exception:
        return {"C": 1.0, "class_weight": "balanced"}  # valores razonables si no hay métricas


def _metricas(y_real: List[str], y_pred: List[str], clases: List[str]) -> Dict[str, Any]:
    """Accuracy, F1 macro/ponderado, métricas por clase y matriz de confusión."""
    reporte = classification_report(y_real, y_pred, labels=clases, output_dict=True, zero_division=0)
    return {
        "accuracy": round(float(accuracy_score(y_real, y_pred)), 4),
        "f1_macro": round(float(f1_score(y_real, y_pred, labels=clases, average="macro", zero_division=0)), 4),
        "f1_weighted": round(float(f1_score(y_real, y_pred, labels=clases, average="weighted", zero_division=0)), 4),
        "por_clase": {
            c: {
                "precision": round(reporte[c]["precision"], 4),
                "recall": round(reporte[c]["recall"], 4),
                "f1": round(reporte[c]["f1-score"], 4),
                "soporte": int(reporte[c]["support"]),
            }
            for c in clases
        },
        "matriz_confusion": confusion_matrix(y_real, y_pred, labels=clases).tolist(),
    }


def limpiar_frases(tablas: List[pd.DataFrame]) -> pd.DataFrame:
    """Une las tablas de frases, quita vacías y duplicadas."""
    datos = pd.concat([t[["texto", "intencion"]] for t in tablas], ignore_index=True)
    datos["texto"] = datos["texto"].fillna("").astype(str).str.strip()
    datos["intencion"] = datos["intencion"].fillna("").astype(str).str.strip().str.lower()
    datos = datos[(datos["texto"] != "") & (datos["intencion"] != "")]
    return datos.drop_duplicates(subset=["texto"]).reset_index(drop=True)


def entrenar_experimento(tablas: List[pd.DataFrame], nombre_archivo: str = "") -> Dict[str, Any]:
    """Entrena un modelo con las frases del archivo y devuelve sus métricas."""
    inicio = time.perf_counter()
    datos = limpiar_frases(tablas)

    # Validaciones: sin esto la división estratificada o el modelo fallarían
    conteo = datos["intencion"].value_counts()
    if len(datos) < MIN_FRASES:
        raise DatosInsuficientes(f"Se necesitan al menos {MIN_FRASES} frases válidas; el archivo tiene {len(datos)}.")
    if len(conteo) < 2:
        raise DatosInsuficientes("Se necesitan al menos 2 intenciones distintas para entrenar.")
    pocas = conteo[conteo < MIN_POR_CLASE]
    if len(pocas):
        raise DatosInsuficientes(
            f"Cada intención necesita al menos {MIN_POR_CLASE} frases. Revisa: {', '.join(pocas.index)}."
        )

    seed = config.get("project", {}).get("seed", 42)
    # El 20 % de prueba debe tener al menos una frase por intención
    test_size = max(0.2, len(conteo) / len(datos))
    X_train, X_test, y_train, y_test = train_test_split(
        datos["texto"], datos["intencion"], test_size=test_size, random_state=seed, stratify=datos["intencion"]
    )

    # Mismo pipeline que producción: fases 1-4 + TF-IDF + regresión logística
    params = _parametros_produccion()
    pipeline = Pipeline([
        ("preprocesamiento", crear_preprocesador(config)),
        ("vectorizador", crear_vectorizador(config)),
        ("modelo", LogisticRegression(max_iter=1000, random_state=seed, **params)),
    ])
    pipeline.fit(X_train, y_train)

    clases = sorted(conteo.index.tolist())
    resultado = {
        "fecha": datetime.now().isoformat(timespec="seconds"),
        "archivo": nombre_archivo,
        "frases": len(datos),
        "muestras_train": len(X_train),
        "muestras_test": len(X_test),
        "distribucion": {c: int(conteo[c]) for c in clases},
        "clases": clases,
        "modelo": "Regresión logística",
        "parametros": params,
        "experimento": _metricas(list(y_test), list(pipeline.predict(X_test)), clases),
        "vocabulario": len(pipeline.named_steps["vectorizador"].vocabulary_),
    }

    # El modelo oficial evaluado con las mismas frases de prueba, para comparar
    resultado["oficial"] = _evaluar_oficial(X_test, y_test, clases)
    resultado["segundos"] = round(time.perf_counter() - inicio, 1)

    RUTA_EXPERIMENTO.parent.mkdir(parents=True, exist_ok=True)
    RUTA_EXPERIMENTO.write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")
    return resultado


def _evaluar_oficial(X_test, y_test, clases: List[str]) -> Dict[str, Any]:
    """Métricas del modelo oficial sobre las frases de prueba del archivo."""
    rel = config.get("artifacts", {}).get("model_path", "artifacts/modelo.joblib")
    ruta = RAIZ_BACKEND / rel
    if not ruta.is_file():
        return {"disponible": False, "motivo": "El modelo oficial todavía no está entrenado."}
    try:
        modelo = joblib.load(ruta)
        y_pred = list(modelo.predict(X_test))
        # Intenciones del archivo que el modelo oficial no conoce
        desconocidas = sorted(set(clases) - set(modelo.classes_))
        return {"disponible": True, "intenciones_desconocidas": desconocidas, **_metricas(list(y_test), y_pred, clases)}
    except Exception as exc:
        return {"disponible": False, "motivo": f"No se pudo evaluar el modelo oficial: {exc}"}


def ultimo_experimento() -> Dict[str, Any]:
    """El último experimento guardado, o {"disponible": False} si no hay."""
    if not RUTA_EXPERIMENTO.is_file():
        return {"disponible": False}
    return {"disponible": True, **json.loads(RUTA_EXPERIMENTO.read_text(encoding="utf-8"))}
