"""Conexión a la base de datos de la tienda.

Con la variable de entorno DATABASE_URL (la define docker-compose) se conecta al
contenedor PostgreSQL. Sin ella usa el archivo SQLite de rutas.base_datos_tienda,
para poder ejecutar el backend y las pruebas sin Docker.
"""

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Sequence

from src.config import config

RAIZ_BACKEND = Path(__file__).resolve().parent.parent.parent


def usa_postgres() -> bool:
    """Indica si el backend está configurado para usar PostgreSQL."""
    return bool(os.environ.get("DATABASE_URL"))


def ruta_sqlite() -> Path:
    """Ruta al archivo SQLite usado cuando no hay DATABASE_URL."""
    rel = config.get("rutas", {}).get("base_datos_tienda", "../database/tienda.db")
    return RAIZ_BACKEND / rel


def descripcion_base() -> str:
    """Texto para diagnóstico: qué base de datos se está usando (sin contraseña)."""
    if usa_postgres():
        url = os.environ["DATABASE_URL"]
        return "postgresql://" + url.split("@", 1)[-1]
    return str(ruta_sqlite())


def consultar(sql: str, parametros: Sequence[Any] = ()) -> List[Dict[str, Any]]:
    """Ejecuta una consulta SELECT y devuelve las filas como diccionarios.

    Los marcadores de parámetros dependen del motor: %s en PostgreSQL y ? en SQLite.
    Lanza una excepción si la base no está disponible.
    """
    if usa_postgres():
        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row, connect_timeout=3) as conn:
            return list(conn.execute(sql, parametros).fetchall())

    ruta = ruta_sqlite()
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe la base de datos SQLite en {ruta}")
    with sqlite3.connect(ruta) as conn:
        conn.row_factory = sqlite3.Row
        return [dict(fila) for fila in conn.execute(sql, parametros).fetchall()]


def tienda_cargada() -> bool:
    """True si la base responde y tiene al menos un producto importado."""
    try:
        filas = consultar("SELECT COUNT(*) AS total FROM productos")
        return int(filas[0]["total"]) > 0
    except Exception:
        return False
