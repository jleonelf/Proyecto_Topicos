"""Fase 6: Inferencia con el Modelo en Producción y Detección OOD.

Responsable: Jorge.
Función principal: predecir(texto)
"""

import os
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import joblib
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Cache del modelo, detector y configuración para no recargar de disco en cada predicción
_MODELO_CACHE = None
_DETECTOR_CACHE = None
_CONFIG_CACHE = None


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


def invalidar_cache():
    """Limpia el caché en memoria del modelo, detector OOD y la configuración."""
    global _MODELO_CACHE, _DETECTOR_CACHE, _CONFIG_CACHE
    _MODELO_CACHE = None
    _DETECTOR_CACHE = None
    _CONFIG_CACHE = None


def obtener_config(config_path: str = "src/config.yaml") -> Dict[str, Any]:
    """Carga y cachea la configuración del sistema."""
    global _CONFIG_CACHE
    if _CONFIG_CACHE is None:
        ruta_res = resolver_ruta(config_path)
        if not os.path.exists(ruta_res):
            return {
                "artifacts": {
                    "model_path": resolver_ruta("artifacts/modelo.joblib"),
                    "ood_detector_path": resolver_ruta("artifacts/ood_detector.joblib")
                },
                "inference": {"umbral": 0.35, "top_k": 3, "usar_detector_ood": True}
            }
        with open(ruta_res, "r", encoding="utf-8") as f:
            _CONFIG_CACHE = yaml.safe_load(f)
    return _CONFIG_CACHE


def cargar_modelo(model_path: Optional[str] = None):
    """Carga y cachea el pipeline entrenado serializado en joblib."""
    global _MODELO_CACHE
    if _MODELO_CACHE is None:
        if model_path is None:
            cfg = obtener_config()
            raw_path = cfg.get("artifacts", {}).get("model_path", "artifacts/modelo.joblib")
            model_path = resolver_ruta(raw_path)
        else:
            model_path = resolver_ruta(model_path)

        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"No se encontró el artefacto del modelo en '{model_path}'. "
                "Ejecute primero: python -m src.models.train"
            )
        _MODELO_CACHE = joblib.load(model_path)
    return _MODELO_CACHE


def cargar_detector(detector_path: Optional[str] = None):
    """Carga y cachea el detector OOD serializado en joblib."""
    global _DETECTOR_CACHE
    if _DETECTOR_CACHE is None:
        if detector_path is None:
            cfg = obtener_config()
            raw_path = cfg.get("artifacts", {}).get("ood_detector_path", "artifacts/ood_detector.joblib")
            detector_path = resolver_ruta(raw_path)
        else:
            detector_path = resolver_ruta(detector_path)

        if not os.path.exists(detector_path):
            raise FileNotFoundError(
                f"No se encontró el detector OOD en '{detector_path}'. "
                "Ejecute primero: python -m src.models.train"
            )
        _DETECTOR_CACHE = joblib.load(detector_path)

    return _DETECTOR_CACHE


def predecir(texto: str, config_path: str = "src/config.yaml") -> Dict[str, Any]:
    """Predice la intención de una frase de usuario integrando detección OOD.

    Devuelve:
        - texto: la consulta recibida.
        - intencion: la clase detectada si supera los criterios OOD, o 'no_entendido' si es rechazada.
        - intencion_detectada: la clase más probable sin aplicar el filtro de rechazo.
        - probabilidad: confianza entre 0.0 y 1.0 de la mejor intención.
        - umbral: valor de umbral de decisión aplicado.
        - confianza_suficiente: booleano indicando si supera el filtro OOD / umbral.
        - top3: las 3 intenciones más probables con sus probabilidades.
    """
    cfg = obtener_config(config_path)
    umbral_default = float(cfg.get("inference", {}).get("umbral", 0.35))
    top_k = int(cfg.get("inference", {}).get("top_k", 3))
    usar_detector = bool(cfg.get("inference", {}).get("usar_detector_ood", True))

    if not isinstance(texto, str) or not texto.strip():
        return {
            "error": "Texto vacío o inválido",
            "texto": texto if isinstance(texto, str) else "",
            "intencion": "desconocido",
            "intencion_detectada": "desconocido",
            "probabilidad": 0.0,
            "umbral": round(umbral_default, 4),
            "top3": [],
            "confianza_suficiente": False
        }

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

    # Detección OOD / Decisión de rechazo
    confianza_suficiente = False
    umbral_aplicado = umbral_default

    if usar_detector:
        detector = cargar_detector()
        try:
            confianza_suficiente = bool(detector.predict_accept([texto])[0])
        except Exception as exc:
            raise RuntimeError("Falló la evaluación del detector OOD; no se emitió una intención.") from exc
        umbral_aplicado = float(getattr(detector, "umbral_prob", getattr(detector, "umbral", umbral_default)))
    else:
        confianza_suficiente = mejor_prob >= umbral_default
        umbral_aplicado = umbral_default

    return {
        "texto": texto,
        "intencion": mejor_clase if confianza_suficiente else "no_entendido",
        "intencion_detectada": mejor_clase,
        "probabilidad": round(mejor_prob, 4),
        "umbral": round(umbral_aplicado, 4),
        "confianza_suficiente": bool(confianza_suficiente),
        "top3": top_lista
    }


if __name__ == "__main__":
    import sys
    ejemplo = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "¿tienen vestidos rojos en talla m?"
    resultado = predecir(ejemplo)
    print("\n--- Resultado de Predicción ---")
    print(yaml.dump(resultado, allow_unicode=True, sort_keys=False))
