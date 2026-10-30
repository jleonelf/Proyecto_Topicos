"""Fase 6: Inferencia con el Modelo en Producción.

Responsable: Jorge.
Función principal: predecir(texto)
"""

import os
from typing import Dict, Any, List, Optional
import yaml
import joblib
import numpy as np


# Cache del modelo para no recargarlo de disco en cada predicción
_MODELO_CACHE = None
_CONFIG_CACHE = None


def obtener_config(config_path: str = "src/config.yaml") -> Dict[str, Any]:
    """Carga y cachea la configuración del sistema."""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        if not os.path.exists(config_path):
            return {
                "artifacts": {"model_path": "artifacts/modelo.joblib"},
                "inference": {"umbral": 0.55, "top_k": 3}
            }
        with open(config_path, "r", encoding="utf-8") as f:
            _CONFIG_CACHE = yaml.safe_load(f)
    return _CONFIG_CACHE


def cargar_modelo(model_path: Optional[str] = None):
    """Carga y cachea el pipeline entrenado serializado en joblib."""
    global _MODELO_CACHE
    if _MODELO_CACHE is None:
        if model_path is None:
            cfg = obtener_config()
            model_path = cfg.get("artifacts", {}).get("model_path", "artifacts/modelo.joblib")
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"No se encontró el artefacto del modelo en '{model_path}'. "
                "Ejecute primero: python -m src.models.train"
            )
        _MODELO_CACHE = joblib.load(model_path)
    return _MODELO_CACHE


def predecir(texto: str, config_path: str = "src/config.yaml") -> Dict[str, Any]:
    """Predice la intención de una frase de usuario.

    Devuelve:
        - intencion: la clase con mayor probabilidad.
        - probabilidad: confianza entre 0.0 y 1.0.
        - top3: las 3 intenciones más probables con sus probabilidades.
        - confianza_suficiente: booleano indicando si supera el umbral configurado.
    """
    if not isinstance(texto, str) or not texto.strip():
        return {
            "error": "Texto vacío o inválido",
            "intencion": "desconocido",
            "probabilidad": 0.0,
            "top3": [],
            "confianza_suficiente": False
        }

    cfg = obtener_config(config_path)
    umbral = cfg.get("inference", {}).get("umbral", 0.55)
    top_k = cfg.get("inference", {}).get("top_k", 3)

    pipeline = cargar_modelo()
    clases = pipeline.classes_

    # Obtener probabilidades
    probabilidades = pipeline.predict_proba([texto])[0]

    # Ordenar índices de mayor a menor probabilidad
    indices_ordenados = np.argsort(probabilidades)[::-1]

    # Mejor predicción
    mejor_idx = indices_ordenados[0]
    mejor_clase = str(clases[mejor_idx])
    mejor_prob = float(probabilidades[mejor_idx])

    # Construir Top K
    top_lista: List[Dict[str, Any]] = []
    for idx in indices_ordenados[:top_k]:
        top_lista.append({
            "intencion": str(clases[idx]),
            "probabilidad": round(float(probabilidades[idx]), 4)
        })

    confianza_suficiente = mejor_prob >= umbral

    return {
        "texto": texto,
        "intencion": mejor_clase if confianza_suficiente else "no_entendido",
        "intencion_detectada": mejor_clase,
        "probabilidad": round(mejor_prob, 4),
        "umbral": umbral,
        "confianza_suficiente": bool(confianza_suficiente),
        "top3": top_lista
    }


if __name__ == "__main__":
    import sys
    ejemplo = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "¿tienen vestidos rojos en talla m?"
    resultado = predecir(ejemplo)
    print("\n--- Resultado de Predicción ---")
    print(yaml.dump(resultado, allow_unicode=True, sort_keys=False))
