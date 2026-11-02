"""Módulo para cargar y acceder a la configuración central del proyecto."""

from pathlib import Path
from typing import Any, Dict
import yaml

# Ruta absoluta al archivo config.yaml
CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


def cargar_config(ruta_archivo: Path = CONFIG_PATH) -> Dict[str, Any]:
    """Carga y parsea el archivo config.yaml.

    Args:
        ruta_archivo: Ruta al archivo YAML de configuración.

    Returns:
        Diccionario con la configuración completa.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        yaml.YAMLError: Si hay un error de sintaxis en el YAML.
    """
    if not ruta_archivo.exists():
        raise FileNotFoundError(f"No se encontró el archivo de configuración en: {ruta_archivo}")

    with open(ruta_archivo, "r", encoding="utf-8") as f:
        configuracion = yaml.safe_load(f)

    return configuracion


# Instancia cargada para acceso directo conveniente
config = cargar_config()
