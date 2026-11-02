"""Carga y división del dataset de intenciones.

Contrato del plan (sección 3.3): cargar_intenciones() y dividir(df, seed=42).
Responsable según el plan: Carmen. Versión provisional para poder entrenar
mientras su implementación no esté en la rama principal.
"""

from pathlib import Path
from typing import Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

RAIZ_BACKEND = Path(__file__).resolve().parent.parent.parent
COLUMNAS = ["texto", "intencion", "rol", "fuente"]  # formato de intenciones.csv (plan, sección 3.2)


def cargar_intenciones(ruta: str = "../database/raw/intenciones.csv") -> pd.DataFrame:
    """Lee intenciones.csv, valida las columnas y limpia filas vacías y duplicadas."""
    ruta = Path(ruta)
    if not ruta.is_absolute() and not ruta.exists():
        ruta = RAIZ_BACKEND / ruta  # rutas relativas a backend/
    df = pd.read_csv(ruta, encoding="utf-8")

    faltantes = {"texto", "intencion"} - set(df.columns)
    if faltantes:
        raise ValueError(f"Al dataset le faltan las columnas {sorted(faltantes)} (esperadas: {COLUMNAS})")

    df["texto"] = df["texto"].astype(str).str.strip()
    df["intencion"] = df["intencion"].astype(str).str.strip()
    df = df[(df["texto"] != "") & (df["texto"].str.lower() != "nan")]  # textos vacíos
    return df.drop_duplicates(subset=["texto"]).reset_index(drop=True)  # la misma frase no puede caer en train y test


def dividir(df: pd.DataFrame, test_size: float = 0.2, seed: int = 42) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
    """División estratificada: cada intención conserva su proporción en train y test.

    Devuelve X_train, X_test, y_train, y_test. La semilla fija hace que la
    división sea siempre la misma (reproducibilidad).
    """
    return train_test_split(
        df["texto"], df["intencion"], test_size=test_size, random_state=seed, stratify=df["intencion"]
    )
