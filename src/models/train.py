"""Fase 6: Script de Entrenamiento Reproducible y Comparación de Modelos con Detección OOD.

Responsable: Jorge.
Ejecución: python -m src.models.train
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple

import yaml
import joblib
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.naive_bayes import ComplementNB
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    classification_report,
    confusion_matrix
)

from src.data.dataset import cargar_intenciones, dividir
from src.nlp.pipeline import TextPreprocessor
from src.nlp.vectorizacion import crear_vectorizador
from src.models.ood import comparar_estrategias

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def resolver_ruta(ruta: str) -> str:
    """Resuelve rutas relativas contra el directorio actual o la raíz del proyecto."""
    p = Path(ruta)
    if p.is_absolute():
        return str(p)
    if p.exists():
        return str(p.resolve())
    candidato = REPO_ROOT / p
    if candidato.exists() or not p.exists():
        return str(candidato.resolve())
    return str(p.resolve())


def cargar_configuracion(config_path: str = "src/config.yaml") -> Dict[str, Any]:
    """Carga los parámetros del archivo YAML asegurando resolución de rutas."""
    ruta_res = resolver_ruta(config_path)
    if not os.path.exists(ruta_res):
        raise FileNotFoundError(f"No se encontró el archivo de configuración: {config_path} ({ruta_res})")
    with open(ruta_res, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def crear_pipeline_base(config: Dict[str, Any], clasificador: Any) -> Pipeline:
    """Construye el scikit-learn Pipeline integrando las 6 fases."""
    nlp_cfg = config.get("nlp", {})
    return Pipeline([
        ("preprocesamiento", TextPreprocessor(
            modo=nlp_cfg.get("modo", "lema"),
            stopwords_extra=nlp_cfg.get("stopwords_extra", ["porfa", "oye", "disculpa", "favor"]),
            stopwords_exclude=nlp_cfg.get("stopwords_exclude", ["no", "sin", "mas", "más"])
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
    """Calcula métricas sobre el conjunto de prueba independiente para reporte final."""
    y_pred = pipeline.predict(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    f1_mac = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    f1_wgt = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_test, y_pred, labels=labels).tolist()

    logger.info(
        f"[{nombre}] Test Accuracy: {acc:.4f} | Test F1 Macro: {f1_mac:.4f} | Test F1 Weighted: {f1_wgt:.4f}"
    )

    return {
        "accuracy": round(acc, 4),
        "f1_macro": round(f1_mac, 4),
        "f1_weighted": round(f1_wgt, 4),
        "classification_report": report,
        "confusion_matrix": cm
    }


def entrenar(config_path: str = "src/config.yaml") -> Tuple[Pipeline, Dict[str, Any]]:
    """Ejecuta el pipeline completo de entrenamiento, evaluación, calibración OOD y persistencia.

    Cumple estrictamente los requisitos metodológicos del proyecto:
    1. Selección de modelo e hiperparámetros basada exclusivamente en validación
       cruzada estratificada (5 folds) sobre el conjunto de entrenamiento (X_train).
    2. Evaluación en conjunto de prueba (X_test) realizada una sola vez para
       informar el rendimiento final sin sesgar decisiones de modelado.
    3. Calibración y selección de detector OOD usando únicamente datos de entrenamiento
       y el conjunto de validación OOD (data/ood_val.csv), sin tocar conjuntos de prueba.
    """
    config = cargar_configuracion(config_path)
    seed = config.get("project", {}).get("seed", 42)
    cv_folds = config.get("models", {}).get("cv_folds", 5)
    scoring = config.get("models", {}).get("scoring", "f1_macro")
    n_jobs = config.get("models", {}).get("n_jobs", 1)

    # 1. Cargar datos
    data_path = resolver_ruta(config.get("data", {}).get("raw_path", "data/raw/intenciones.csv"))
    test_size = config.get("data", {}).get("test_size", 0.2)
    logger.info(f"Cargando dataset desde: {data_path}")
    df = cargar_intenciones(data_path)
    logger.info(f"Total de registros: {len(df)} | Clases únicas: {df['intencion'].nunique()}")

    # 2. División estratificada
    X_train, X_test, y_train, y_test = dividir(df, test_size=test_size, seed=seed)
    logger.info(f"Train: {len(X_train)} ejemplos | Test: {len(X_test)} ejemplos")

    clases = sorted(df["intencion"].unique().tolist())
    skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=seed)
    resultados: Dict[str, Any] = {
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
    logger.info("--- Evaluando Modelo 1: Línea Base (Dummy Most Frequent) ---")
    pipe_dummy = crear_pipeline_base(config, DummyClassifier(strategy="most_frequent"))
    pipe_dummy.fit(X_train, y_train)
    res_dummy = evaluar_modelo("DummyClassifier", pipe_dummy, X_test, y_test, clases)
    resultados["modelos"]["dummy_baseline"] = {
        "descripcion": "Línea base que predice siempre la clase mayoritaria",
        "cv_score": 0.0,
        "metricas": res_dummy
    }

    # ==========================================================
    # Modelo 2: Naive Bayes (ComplementNB) con GridSearchCV
    # ==========================================================
    logger.info("--- Optimizando Modelo 2: Naive Bayes (ComplementNB) con CV ---")
    pipe_nb = crear_pipeline_base(config, ComplementNB())
    nb_grid_params = config.get("models", {}).get("naive_bayes", {}).get("param_grid", {
        "modelo__alpha": [0.1, 0.5, 1.0, 2.0]
    })
    grid_nb = GridSearchCV(
        pipe_nb,
        param_grid=nb_grid_params,
        cv=skf,
        scoring=scoring,
        n_jobs=n_jobs
    )
    grid_nb.fit(X_train, y_train)
    cv_score_nb = round(float(grid_nb.best_score_), 4)
    logger.info(f"Naive Bayes - Mejor CV Score ({scoring}): {cv_score_nb:.4f} con {grid_nb.best_params_}")

    # ==========================================================
    # Modelo 3: Regresión Logística con GridSearchCV
    # ==========================================================
    logger.info("--- Optimizando Modelo 3: Regresión Logística con CV ---")
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
        n_jobs=n_jobs
    )
    grid_lr.fit(X_train, y_train)
    cv_score_lr = round(float(grid_lr.best_score_), 4)
    logger.info(f"Regresión Logística - Mejor CV Score ({scoring}): {cv_score_lr:.4f} con {grid_lr.best_params_}")

    # ==========================================================
    # Selección del Modelo Ganador mediante Validación Cruzada
    # ==========================================================
    if cv_score_lr >= cv_score_nb:
        ganador_nombre = "regresion_logistica"
        ganador_pipe = grid_lr.best_estimator_
        mejor_cv_score = cv_score_lr
        logger.info(
            f"Modelo ganador seleccionado por CV ({scoring}): Regresión Logística "
            f"({cv_score_lr:.4f} vs NB: {cv_score_nb:.4f})"
        )
    else:
        ganador_nombre = "naive_bayes"
        ganador_pipe = grid_nb.best_estimator_
        mejor_cv_score = cv_score_nb
        logger.info(
            f"Modelo ganador seleccionado por CV ({scoring}): Naive Bayes "
            f"({cv_score_nb:.4f} vs LR: {cv_score_lr:.4f})"
        )

    # ==========================================================
    # Evaluación Final Única en Conjunto de Prueba Independiente
    # ==========================================================
    logger.info("--- Evaluando modelos en conjunto de prueba independiente (evaluación final única) ---")
    res_nb = evaluar_modelo("NaiveBayes", grid_nb.best_estimator_, X_test, y_test, clases)
    res_lr = evaluar_modelo("RegresionLogistica", grid_lr.best_estimator_, X_test, y_test, clases)

    resultados["modelos"]["naive_bayes"] = {
        "descripcion": "Naive Bayes (ComplementNB) optimizado con Stratified 5-Fold CV",
        "mejores_parametros": grid_nb.best_params_,
        "mejor_cv_score": cv_score_nb,
        "metricas": res_nb
    }

    resultados["modelos"]["regresion_logistica"] = {
        "descripcion": "Regresión Logística multinomial optimizada con Stratified 5-Fold CV",
        "mejores_parametros": {
            k: (v if v is not None else "None") for k, v in grid_lr.best_params_.items()
        },
        "mejor_cv_score": cv_score_lr,
        "metricas": res_lr
    }

    res_ganador = res_lr if ganador_nombre == "regresion_logistica" else res_nb
    resultados["modelo_produccion"] = {
        "nombre": ganador_nombre,
        "criterio": "Mayor F1 Macro en validación cruzada estratificada de 5 folds sobre X_train",
        "mejor_cv_score": mejor_cv_score,
        "test_f1_macro": res_ganador["f1_macro"],
        "test_accuracy": res_ganador["accuracy"]
    }

    # ==========================================================
    # Fase OOD: Comparación Cuantitativa y Calibración de Detectores
    # (Usa exclusivamente datos de entrenamiento y data/ood_val.csv;
    #  NUNCA toca X_test ni data/ood_test.csv)
    # ==========================================================
    logger.info("--- Evaluando y calibrando estrategias de rechazo OOD en validación ---")
    ood_val_path = resolver_ruta(config.get("data", {}).get("ood_val_path", "data/ood_val.csv"))
    if not os.path.exists(ood_val_path):
        raise FileNotFoundError(f"No se encontró el dataset OOD de validación en: {ood_val_path}")

    df_ood_val = pd.read_csv(ood_val_path)
    logger.info(f"Dataset OOD de validación cargado ({len(df_ood_val)} consultas) desde {ood_val_path}")

    # Partición interna de validación a partir de X_train (sin tocar X_test)
    X_tr_inner, X_val_inner, y_tr_inner, y_val_inner = train_test_split(
        X_train,
        y_train,
        test_size=0.2,
        random_state=seed,
        stratify=y_train
    )

    # Entrenar una copia del pipeline en X_tr_inner para evaluación honesta en X_val_inner
    pipe_val = crear_pipeline_base(config, clone(ganador_pipe.named_steps["modelo"]))
    pipe_val.fit(X_tr_inner, y_tr_inner)

    resultados_ood = comparar_estrategias(
        pipeline=pipe_val,
        X_train=X_tr_inner,
        y_train=y_tr_inner,
        X_val_id=X_val_inner,
        y_val_id=y_val_inner,
        X_val_ood=df_ood_val["texto"]
    )

    detector_ganador = resultados_ood["detector_seleccionado"]
    logger.info(
        f"Estrategia OOD ganadora seleccionada: {resultados_ood['estrategia_seleccionada']} "
        f"| Resumen: {resultados_ood['resumen_ganador']}"
    )

    # Reajustar el detector ganador sobre todo X_train con el pipeline de producción final
    detector_ganador.fit(ganador_pipe, X_train, y_train)

    # Registrar en métricas
    resultados["estrategias_rechazo_ood"] = {
        "tabla_comparativa": resultados_ood["tabla_comparativa"],
        "estrategia_seleccionada": resultados_ood["estrategia_seleccionada"],
        "resumen_ganador": resultados_ood["resumen_ganador"],
        "justificacion": resultados_ood.get("justificacion", "")
    }

    # ==========================================================
    # Persistencia de Artefactos
    # ==========================================================
    art_cfg = config.get("artifacts", {})
    model_path = resolver_ruta(art_cfg.get("model_path", "artifacts/modelo.joblib"))
    ood_path = resolver_ruta(art_cfg.get("ood_detector_path", "artifacts/ood_detector.joblib"))
    metrics_path = resolver_ruta(art_cfg.get("metrics_path", "artifacts/metricas.json"))

    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    os.makedirs(os.path.dirname(ood_path), exist_ok=True)
    os.makedirs(os.path.dirname(metrics_path), exist_ok=True)

    joblib.dump(ganador_pipe, model_path)
    logger.info(f"Artefacto serializado del modelo guardado en: {model_path}")

    joblib.dump(detector_ganador, ood_path)
    logger.info(f"Artefacto serializado del detector OOD guardado en: {ood_path}")

    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    logger.info(f"Métricas y comparación guardadas en: {metrics_path}")

    # Invalidar caché de inferencia para recargar nuevo modelo y detector
    try:
        from src.models.predict import invalidar_cache
        invalidar_cache()
    except Exception:
        pass

    return ganador_pipe, resultados


if __name__ == "__main__":
    entrenar()
