"""Módulo de carga y división de datasets.

Responsable: Carmen.
"""

from typing import Tuple
import pandas as pd
from sklearn.model_selection import train_test_split


def cargar_intenciones(path: str = "data/raw/intenciones.csv") -> pd.DataFrame:
    """Carga el dataset de intenciones desde un archivo CSV."""
    df = pd.read_csv(path)
    df = df.dropna(subset=["texto", "intencion"])
    df["texto"] = df["texto"].astype(str)
    df["intencion"] = df["intencion"].astype(str)
    return df


def dividir(
    df: pd.DataFrame,
    test_size: float = 0.2,
    seed: int = 42
) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """Realiza una división estratificada de entrenamiento y prueba."""
    X = df["texto"]
    y = df["intencion"]

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        random_state=seed,
        stratify=y
    )
    return X_train, X_test, y_train, y_test
