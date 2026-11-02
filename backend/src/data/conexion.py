"""Conexión a la base de datos de la tienda.

Con la variable de entorno DATABASE_URL (la define docker-compose) se conecta al
contenedor PostgreSQL. Sin ella usa el archivo SQLite de rutas.base_datos_tienda,
para poder ejecutar el backend y las pruebas sin Docker.

Las consultas se escriben siempre con "?" como marcador de parámetros; para
PostgreSQL se traducen a "%s" automáticamente. Así el mismo SQL sirve en ambos.
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence

from src.config import config

# Carpeta backend/: las rutas de config.yaml son relativas a ella
RAIZ_BACKEND = Path(__file__).resolve().parent.parent.parent

# Esquema equivalente a database/init/01_esquema.sql, adaptado a SQLite
# (sin SERIAL ni JSONB). Solo se usa cuando se trabaja sin Docker.
ESQUEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS productos (
    sku        TEXT PRIMARY KEY,
    nombre     TEXT NOT NULL,
    categoria  TEXT NOT NULL,
    talla      TEXT,
    color      TEXT,
    precio     REAL NOT NULL CHECK (precio >= 0),
    stock      INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0)
);
CREATE TABLE IF NOT EXISTS ventas (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha            TEXT NOT NULL,
    sku              TEXT NOT NULL REFERENCES productos (sku),
    cantidad         INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario  REAL NOT NULL CHECK (precio_unitario >= 0)
);
CREATE TABLE IF NOT EXISTS tienda (
    id            INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    nombre        TEXT NOT NULL,
    direccion     TEXT,
    horarios      TEXT,
    envios        TEXT,
    devoluciones  TEXT,
    metodos_pago  TEXT
);
"""


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
        return "postgresql://" + url.split("@", 1)[-1]  # se omite usuario:clave@
    return str(ruta_sqlite())


def _sql(sql: str) -> str:
    """Adapta los marcadores "?" al motor en uso."""
    return sql.replace("?", "%s") if usa_postgres() else sql


def consultar(sql: str, parametros: Sequence[Any] = ()) -> List[Dict[str, Any]]:
    """Ejecuta una consulta SELECT y devuelve las filas como diccionarios.

    Lanza una excepción si la base no está disponible.
    """
    if usa_postgres():
        import psycopg
        from psycopg.rows import dict_row

        # dict_row: cada fila llega como {"columna": valor}
        with psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row, connect_timeout=3) as conn:
            return list(conn.execute(_sql(sql), parametros).fetchall())

    ruta = ruta_sqlite()
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe la base de datos SQLite en {ruta}")
    with sqlite3.connect(ruta) as conn:
        conn.row_factory = sqlite3.Row  # permite convertir cada fila en diccionario
        return [dict(fila) for fila in conn.execute(sql, parametros).fetchall()]


class _Transaccion:
    """Envoltorio mínimo sobre una conexión abierta para escribir en la base."""

    def __init__(self, conexion):
        self._conexion = conexion

    def ejecutar(self, sql: str, parametros: Sequence[Any] = ()) -> None:
        """Ejecuta una sentencia (INSERT, UPDATE, DELETE...)."""
        self._conexion.execute(_sql(sql), parametros)

    def ejecutar_muchos(self, sql: str, filas: Iterable[Sequence[Any]]) -> None:
        """Ejecuta la misma sentencia para cada fila (inserción masiva)."""
        filas = list(filas)
        if not filas:
            return
        if usa_postgres():
            with self._conexion.cursor() as cursor:
                cursor.executemany(_sql(sql), filas)
        else:
            self._conexion.executemany(sql, filas)


@contextmanager
def transaccion():
    """Abre una transacción: si algo falla dentro del bloque, no se guarda nada.

    Uso:
        with transaccion() as t:
            t.ejecutar_muchos("INSERT INTO ventas (...) VALUES (?, ?)", filas)
    """
    if usa_postgres():
        import psycopg

        # Al salir del "with" sin errores psycopg hace COMMIT; con error, ROLLBACK
        with psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=3) as conn:
            yield _Transaccion(conn)
        return

    ruta = ruta_sqlite()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(ruta)
    try:
        conn.execute("PRAGMA foreign_keys = ON")  # SQLite no valida claves foráneas por defecto
        conn.executescript(ESQUEMA_SQLITE)  # crea las tablas si es la primera vez
        yield _Transaccion(conn)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def tienda_cargada() -> bool:
    """True si la base responde y tiene al menos un producto importado."""
    try:
        filas = consultar("SELECT COUNT(*) AS total FROM productos")
        return int(filas[0]["total"]) > 0
    except Exception:
        return False
