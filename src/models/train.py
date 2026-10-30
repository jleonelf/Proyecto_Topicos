"""Fase 6: Script de Entrenamiento Reproducible y Comparación de Modelos.

Responsable: Jorge.
Ejecución: python -m src.models.train
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Tuple

import yaml
import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.dummy import DummyClassifier
from sklearn.naive_bayes import ComplementNB
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix
)

from src.data.dataset import cargar_intenciones, dividir
from src.nlp.pipeline import TextPreprocessor
from src.nlp.vectorizacion import crear_vectorizador

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def cargar_configuracion(config_path: str = "src/config.yaml") -> Dict[str, Any]:
    """Carga los parámetros del archivo YAML."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"No se encontró el archivo de configuración: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def crear_pipeline_base(config: Dict[str, Any], clasificador: Any) -> Pipeline:
    """Construye el scikit-learn Pipeline integrando las 6 fases."""
    nlp_cfg = config.get("nlp", {})
    return Pipeline([
        ("preprocesamiento", TextPreprocessor(
            modo=nlp_cfg.get("modo", "lema"),
            stopwords_extra=nlp_cfg.get("stopwords_extra", []),
            stopwords_exclude=nlp_cfg.get("stopwords_exclude", [])
        )),
        ("vectorizador", crear_vectorizador(config)),
        ("modelo", clasificador)
    ])


def evaluar_modelo(
    nombre: str,
    pipeline: Pipeline,
    X_test: pd.Series,
    y_test: pd.Series,
    labels: list
) -> Dict[str, Any]:
    """Calcula métricas rigurosas sobre el conjunto de prueba."""
    y_pred = pipeline.predict(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    f1_mac = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    f1_wgt = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=labels).tolist()

    logger.info(
        f"[{nombre}] Accuracy: {acc:.4f} | F1 Macro: {f1_mac:.4f} | F1 Weighted: {f1_wgt:.4f}"
    )

    return {
        "accuracy": round(acc, 4),
        "f1_macro": round(f1_mac, 4),
        "f1_weighted": round(f1_wgt, 4),
        "classification_report": report,
        "confusion_matrix": cm
    }


def entrenar(config_path: str = "src/config.yaml") -> Tuple[Pipeline, Dict[str, Any]]:
    """Ejecuta el pipeline completo de entrenamiento, evaluación y persistencia."""
    config = cargar_configuracion(config_path)
    seed = config.get("project", {}).get("seed", 42)
    cv_folds = config.get("models", {}).get("cv_folds", 5)
    scoring = config.get("models", {}).get("scoring", "f1_macro")

    # 1. Cargar datos
    data_path = config.get("data", {}).get("raw_path", "data/raw/intenciones.csv")
    test_size = config.get("data", {}).get("test_size", 0.2)
    logger.info(f"Cargando dataset desde: {data_path}")
    df = cargar_intenciones(data_path)
    logger.info(f"Total de registros: {len(df)} | Clases únicas: {df['intencion'].nunique()}")

    # 2. División estratificada
    X_train, X_test, y_train, y_test = dividir(df, test_size=test_size, seed=seed)
    logger.info(f"Train: {len(X_train)} ejemplos | Test: {len(X_test)} ejemplos")

    clases = sorted(df["intencion"].unique().tolist())
    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=seed)
    resultados = {
        "fecha_entrenamiento": datetime.now().isoformat(),
        "configuracion": config,
        "total_muestras": len(df),
        "muestras_train": len(X_train),
        "muestras_test": len(X_test),
        "clases": clases,
        "modelos": {}
    }

    # ==========================================================
    # Modelo 1: Línea Base (Dummy - Clase más frecuente)
    # ==========================================================
    logger.info("--- Entrenando Modelo 1: Línea Base (Dummy Most Frequent) ---")
    pipe_dummy = crear_pipeline_base(config, DummyClassifier(strategy="most_frequent"))
    pipe_dummy.fit(X_train, y_train)
    res_dummy = evaluar_modelo("DummyClassifier", pipe_dummy, X_test, y_test, clases)
    resultados["modelos"]["dummy_baseline"] = {
        "descripcion": "Línea base que predice siempre la clase mayoritaria",
        "metricas": res_dummy
    }

    # ==========================================================
    # Modelo 2: Naive Bayes (ComplementNB) con GridSearchCV
    # ==========================================================
    logger.info("--- Entrenando Modelo 2: Naive Bayes (ComplementNB) ---")
    pipe_nb = crear_pipeline_base(config, ComplementNB())
    nb_grid_params = config.get("models", {}).get("naive_bayes", {}).get("param_grid", {
        "modelo__alpha": [0.1, 0.5, 1.0, 2.0]
    })
    grid_nb = GridSearchCV(
        pipe_nb,
        param_grid=nb_grid_params,
        cv=skf,
        scoring=scoring,
        n_jobs=-1
    )
    grid_nb.fit(X_train, y_train)
    logger.info(f"Mejores hiperparámetros Naive Bayes: {grid_nb.best_params_}")
    res_nb = evaluar_modelo("NaiveBayes", grid_nb.best_estimator_, X_test, y_test, clases)
    resultados["modelos"]["naive_bayes"] = {
        "descripcion": "Naive Bayes (ComplementNB) optimizado con GridSearchCV",
        "mejores_parametros": grid_nb.best_params_,
        "mejor_cv_score": round(float(grid_nb.best_score_), 4),
        "metricas": res_nb
    }

    # ==========================================================
    # Modelo 3: Regresión Logística con GridSearchCV
    # ==========================================================
    logger.info("--- Entrenando Modelo 3: Regresión Logística ---")
    lr_fixed = config.get("models", {}).get("logistic_regression", {}).get("fixed_params", {
        "max_iter": 1000,
        "solver": "lbfgs",
        "random_state": seed
    })
    pipe_lr = crear_pipeline_base(config, LogisticRegression(**lr_fixed))
    lr_grid_params = config.get("models", {}).get("logistic_regression", {}).get("param_grid", {
        "modelo__C": [0.1, 1.0, 5.0, 10.0],
        "modelo__class_weight": [None, "balanced"]
    })
    grid_lr = GridSearchCV(
        pipe_lr,
        param_grid=lr_grid_params,
        cv=skf,
        scoring=scoring,
        n_jobs=-1
    )
    grid_lr.fit(X_train, y_train)
    logger.info(f"Mejores hiperparámetros Regresión Logística: {grid_lr.best_params_}")
    res_lr = evaluar_modelo("RegresionLogistica", grid_lr.best_estimator_, X_test, y_test, clases)
    resultados["modelos"]["regresion_logistica"] = {
        "descripcion": "Regresión Logística multinomial optimizada con GridSearchCV",
        "mejores_parametros": {
            k: (v if v is not None else "None") for k, v in grid_lr.best_params_.items()
        },
        "mejor_cv_score": round(float(grid_lr.best_score_), 4),
        "metricas": res_lr
    }

    # ==========================================================
    # Selección del Ganador para Producción
    # ==========================================================
    f1_lr = res_lr["f1_macro"]
    f1_nb = res_nb["f1_macro"]

    if f1_lr >= f1_nb:
        ganador_nombre = "regresion_logistica"
        ganador_pipe = grid_lr.best_estimator_
        logger.info(f"Modelo seleccionado para producción: Regresión Logística (F1 Macro: {f1_lr:.4f})")
    else:
        ganador_nombre = "naive_bayes"
        ganador_pipe = grid_nb.best_estimator_
        logger.info(f"Modelo seleccionado para producción: Naive Bayes (F1 Macro: {f1_nb:.4f})")

    resultados["modelo_produccion"] = {
        "nombre": ganador_nombre,
        "criterio": "Mayor F1 Macro en conjunto de prueba",
        "f1_macro": max(f1_lr, f1_nb)
    }

    # ==========================================================
    # Persistencia de Artefactos
    # ==========================================================
    art_cfg = config.get("artifacts", {})
    model_path = art_cfg.get("model_path", "artifacts/modelo.joblib")
    metrics_path = art_cfg.get("metrics_path", "artifacts/metricas.json")

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    os.makedirs(os.path.dirname(metrics_path), exist_ok=True)

    # Guardar modelo completo (pipeline de 6 fases)
    joblib.dump(ganador_pipe, model_path)
    logger.info(f"Artefacto serializado guardado en: {model_path}")

    # Guardar métricas en JSON
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    logger.info(f"Métricas y comparación guardadas en: {metrics_path}")

    return ganador_pipe, resultados


if __name__ == "__main__":
    entrenar()
