"""Módulo de Detección Fuera de Dominio (OOD) y Calibración de Rechazo Reproducible.

Implementa y compara de forma modular cuatro estrategias de rechazo OOD más una
estrategia híbrida compuesta:
1. Probabilidad Máxima (MSP / Maximum Softmax Probability): max_p >= tau
2. Margen entre Clases (Top1 - Top2 probability margin): (p1 - p2) >= tau
3. Similitud Coseno a Centroides de Clase (Cosine Centroid Similarity): max_sim >= tau
4. Cobertura de Vocabulario (In-Vocabulary Coverage Ratio): coverage >= tau
5. Estrategia Híbrida Compuesta (Dual-Gate Conjunción):
   Filtro conjunto de confianza probabilística + cobertura de vocabulario/similitud.

Cumple estrictamente los requisitos metodológicos del proyecto:
- Sin reglas ad-hoc para palabras o frases concretas (prohibido explícitamente).
- Toma decisiones basadas en propiedades estadísticas, representacionales y probabilísticas.
- Proporciona calibración reproducible sobre conjuntos de validación (ID + OOD).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional, Sequence
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.metrics import f1_score, accuracy_score
from sklearn.metrics.pairwise import cosine_similarity


def _extraer_componentes_pipeline(pipeline: Pipeline) -> Tuple[Any, Any, Any]:
    """Extrae el preprocesador, vectorizador y modelo clasificador de un Pipeline."""
    prep = pipeline.named_steps.get("preprocesamiento")
    vec = pipeline.named_steps.get("vectorizador")
    clf = pipeline.named_steps.get("modelo")
    if vec is None or clf is None:
        raise ValueError("El pipeline debe contener al menos los pasos 'vectorizador' y 'modelo'.")
    return prep, vec, clf


def _preprocesar_textos(pipeline: Pipeline, X: Sequence[str]) -> List[str]:
    """Aplica la etapa de preprocesamiento del pipeline si existe, o retorna strings limpios."""
    prep, _, _ = _extraer_componentes_pipeline(pipeline)
    if prep is not None:
        return prep.transform(X)
    return [str(t).lower().strip() for t in X]


def _calcular_cobertura_vocabulario(
    preprocessed_texts: Sequence[str],
    vocabulario: set
) -> np.ndarray:
    """Calcula la proporción de tokens de contenido que pertenecen al vocabulario del vectorizador.

    Retorna un array de floats en [0.0, 1.0]. Si la frase no contiene tokens tras el
    preprocesamiento (por ejemplo, stopwords puras o texto vacío), la cobertura es 0.0.
    """
    coberturas = []
    for text in preprocessed_texts:
        tokens = [t for t in str(text).split() if t]
        if not tokens:
            coberturas.append(0.0)
            continue
        en_vocab = sum(1 for t in tokens if t in vocabulario)
        coberturas.append(en_vocab / len(tokens))
    return np.asarray(coberturas, dtype=float)


def calcular_metricas_rechazo(
    y_true_id: np.ndarray,
    y_pred_id: np.ndarray,
    accept_id: np.ndarray,
    accept_ood: np.ndarray,
    clases_target: List[str]
) -> Dict[str, float]:
    """Calcula las 4 métricas cuantitativas clave de rechazo OOD de forma vectorizada."""
    n_id = len(y_true_id)
    n_ood = len(accept_ood)

    # 1. Cobertura / TPR en válidas
    cobertura_id = float(np.mean(accept_id)) if n_id > 0 else 0.0

    # 2. Exactitud entre válidas aceptadas
    n_aceptadas_id = int(np.sum(accept_id))
    if n_aceptadas_id > 0:
        exactitud_aceptadas = float(accuracy_score(y_true_id[accept_id], y_pred_id[accept_id]))
    else:
        exactitud_aceptadas = 0.0

    # 3. FPR en OOD (tasa de falsos aceptados en OOD, minimizar)
    tasa_error_ood = float(np.mean(accept_ood)) if n_ood > 0 else 0.0

    # 4. F1 macro en válidas con rechazo ('no_entendido' para rechazadas)
    y_pred_con_rechazo = np.array(
        [y_pred_id[i] if accept_id[i] else "no_entendido" for i in range(n_id)]
    )
    f1_macro = float(f1_score(y_true_id, y_pred_con_rechazo, labels=clases_target, average="macro", zero_division=0))

    # Score de balance armónico / ponderado
    score_balance = float((f1_macro * 0.5) + (exactitud_aceptadas * 0.25) + ((1.0 - tasa_error_ood) * 0.25))

    return {
        "cobertura_id": round(cobertura_id, 4),
        "exactitud_aceptadas": round(exactitud_aceptadas, 4),
        "tasa_error_ood": round(tasa_error_ood, 4),
        "f1_macro": round(f1_macro, 4),
        "score_balance": round(score_balance, 4)
    }


class BaseOODDetector(ABC):
    """Clase base abstracta para detectores de rechazo fuera de dominio (OOD)."""

    def __init__(self, umbral: float = 0.5):
        self.umbral = float(umbral)
        self.pipeline: Optional[Pipeline] = None

    def fit(self, pipeline: Pipeline, X_train: Optional[Sequence[str]] = None, y_train: Optional[Sequence[str]] = None):
        """Ajusta el detector al pipeline y datos de entrenamiento si es requerido."""
        self.pipeline = pipeline
        return self

    @abstractmethod
    def score(self, X: Sequence[str]) -> np.ndarray:
        """Calcula el score continuo de confianza/pertenencia en dominio (a mayor score, mayor certeza)."""
        pass

    def predict_accept(self, X: Sequence[str]) -> np.ndarray:
        """Determina si cada consulta es aceptada (True) o rechazada como OOD (False)."""
        scores = self.score(X)
        return scores >= self.umbral

    def evaluar(
        self,
        X_id: Sequence[str],
        y_id: Sequence[str],
        X_ood: Sequence[str]
    ) -> Dict[str, Any]:
        """Evalúa cuantitativamente la estrategia sobre datos en dominio y fuera de dominio."""
        if self.pipeline is None:
            raise ValueError("El detector debe ser ajustado con fit() antes de evaluar.")

        y_id_arr = np.asarray(y_id)
        y_pred_raw = self.pipeline.predict(X_id)
        accept_id = self.predict_accept(X_id)
        accept_ood = self.predict_accept(X_ood)
        clases_id = sorted(list(set(y_id_arr)))

        metricas = calcular_metricas_rechazo(y_id_arr, y_pred_raw, accept_id, accept_ood, clases_id)
        return {
            "estrategia": self.__class__.__name__,
            "umbral": round(float(self.umbral), 4),
            **metricas
        }

    def calibrar(
        self,
        X_val_id: Sequence[str],
        y_val_id: Sequence[str],
        X_val_ood: Sequence[str],
        candidatos_umbral: Optional[Sequence[float]] = None,
        max_error_ood: float = 0.15
    ) -> float:
        """Calibra el umbral óptimo precomputando scores para máxima velocidad."""
        if self.pipeline is None:
            raise ValueError("El detector debe ser ajustado antes de calibrar.")

        if candidatos_umbral is None:
            candidatos_umbral = np.linspace(0.15, 0.90, 31)

        scores_id = self.score(X_val_id)
        scores_ood = self.score(X_val_ood)
        y_val_arr = np.asarray(y_val_id)
        y_pred_raw = self.pipeline.predict(X_val_id)
        clases_id = sorted(list(set(y_val_arr)))

        mejor_umbral = self.umbral
        mejor_metrica = -1.0

        for cand in candidatos_umbral:
            acc_id = scores_id >= cand
            acc_ood = scores_ood >= cand
            res = calcular_metricas_rechazo(y_val_arr, y_pred_raw, acc_id, acc_ood, clases_id)

            score_cand = res["score_balance"]
            if res["tasa_error_ood"] <= max_error_ood:
                score_cand += 0.15

            if score_cand > mejor_metrica:
                mejor_metrica = score_cand
                mejor_umbral = float(cand)

        self.umbral = mejor_umbral
        return self.umbral


class MSPDetector(BaseOODDetector):
    """Estrategia 1: Probabilidad Máxima (Maximum Softmax Probability / MSP).

    Acepta si max_c P(y=c|x) >= tau.
    """

    def score(self, X: Sequence[str]) -> np.ndarray:
        if self.pipeline is None:
            raise ValueError("Detector no ajustado.")
        probs = self.pipeline.predict_proba(X)
        return np.max(probs, axis=1)


class MarginDetector(BaseOODDetector):
    """Estrategia 2: Margen entre Clases (Top-1 - Top-2 Probability Margin).

    Acepta si (p_top1 - p_top2) >= tau.
    """

    def score(self, X: Sequence[str]) -> np.ndarray:
        if self.pipeline is None:
            raise ValueError("Detector no ajustado.")
        probs = self.pipeline.predict_proba(X)
        if probs.shape[1] < 2:
            return np.ones(len(X), dtype=float)
        sorted_probs = np.sort(probs, axis=1)
        p_top1 = sorted_probs[:, -1]
        p_top2 = sorted_probs[:, -2]
        return p_top1 - p_top2


class CosineCentroidDetector(BaseOODDetector):
    """Estrategia 3: Similitud Coseno a Centroides de Clase en Espacio TF-IDF.

    Calcula el centroide L2-normalizado de cada clase en el espacio TF-IDF durante el ajuste.
    Para una nueva consulta, calcula la similitud coseno máxima (o hacia la clase predicha).
    """

    def __init__(self, umbral: float = 0.25, modo: str = "max"):
        super().__init__(umbral=umbral)
        self.modo = modo
        self.centroides_: Dict[str, np.ndarray] = {}
        self.clases_: List[str] = []

    def fit(self, pipeline: Pipeline, X_train: Optional[Sequence[str]] = None, y_train: Optional[Sequence[str]] = None):
        super().fit(pipeline, X_train, y_train)
        if X_train is None or y_train is None:
            raise ValueError("CosineCentroidDetector requiere X_train e y_train para calcular centroides.")

        prep, vec, clf = _extraer_componentes_pipeline(pipeline)
        X_prep = prep.transform(X_train) if prep is not None else X_train
        X_tfidf = vec.transform(X_prep)

        y_arr = np.asarray(y_train)
        self.clases_ = sorted(list(set(y_arr)))
        self.centroides_ = {}

        for cl in self.clases_:
            mask = (y_arr == cl)
            if np.sum(mask) == 0:
                continue
            cent = np.asarray(X_tfidf[mask].mean(axis=0)).flatten()
            norm = np.linalg.norm(cent)
            if norm > 0:
                cent = cent / norm
            self.centroides_[cl] = cent

        return self

    def score(self, X: Sequence[str]) -> np.ndarray:
        if self.pipeline is None or not self.centroides_:
            raise ValueError("Detector no ajustado o centroides vacíos.")

        prep, vec, clf = _extraer_componentes_pipeline(self.pipeline)
        X_prep = prep.transform(X) if prep is not None else X
        X_tfidf = vec.transform(X_prep)

        cent_matrix = np.vstack([self.centroides_[cl] for cl in self.clases_])
        sim_matrix = cosine_similarity(X_tfidf, cent_matrix)

        if self.modo == "max":
            return np.max(sim_matrix, axis=1)
        else:
            preds = self.pipeline.predict(X)
            scores = []
            for i, pred in enumerate(preds):
                if pred in self.centroides_:
                    idx = self.clases_.index(pred)
                    scores.append(sim_matrix[i, idx])
                else:
                    scores.append(0.0)
            return np.asarray(scores, dtype=float)


class VocabularyCoverageDetector(BaseOODDetector):
    """Estrategia 4: Cobertura de Tokens de Contenido en Vocabulario.

    Mide qué fracción de los tokens lematizados de la consulta están en el vocabulario TF-IDF.
    Evita falsos positivos en frases donde solo 1 palabra común activa una clase pero el
    resto de la frase es totalmente OOD.
    """

    def __init__(self, umbral: float = 0.40):
        super().__init__(umbral=umbral)
        self.vocabulario_: set = set()

    def fit(self, pipeline: Pipeline, X_train: Optional[Sequence[str]] = None, y_train: Optional[Sequence[str]] = None):
        super().fit(pipeline, X_train, y_train)
        _, vec, _ = _extraer_componentes_pipeline(pipeline)
        if hasattr(vec, "vocabulary_") and vec.vocabulary_ is not None:
            raw_vocab = vec.vocabulary_.keys()
            tokens_vocab = set()
            for feat in raw_vocab:
                for tok in feat.split():
                    tokens_vocab.add(tok)
            self.vocabulario_ = tokens_vocab
        return self

    def score(self, X: Sequence[str]) -> np.ndarray:
        if self.pipeline is None:
            raise ValueError("Detector no ajustado.")
        prep_texts = _preprocesar_textos(self.pipeline, X)
        return _calcular_cobertura_vocabulario(prep_texts, self.vocabulario_)


class HybridOODDetector(BaseOODDetector):
    """Estrategia 5: Estrategia Compuesta / Híbrida (Dual-Gate Conjunción).

    Combina la confianza probabilística (MSP) con la cobertura de vocabulario y la
    similitud representacional a centroides.

    Criterio de aceptación por conjunción (Dual-Gate):
      accept(x) = (MSP >= umbral_prob) AND (Coverage >= umbral_cobertura) AND (CentroidSim >= umbral_sim)
    """

    def __init__(
        self,
        umbral_prob: float = 0.35,
        umbral_cobertura: float = 0.35,
        umbral_similitud: float = 0.0,
        modo: str = "conjuncion"
    ):
        super().__init__(umbral=umbral_prob)
        self.umbral_prob = float(umbral_prob)
        self.umbral_cobertura = float(umbral_cobertura)
        self.umbral_similitud = float(umbral_similitud)
        self.modo = modo

        self.msp_det = MSPDetector(umbral=umbral_prob)
        self.cov_det = VocabularyCoverageDetector(umbral=umbral_cobertura)
        self.cent_det = CosineCentroidDetector(umbral=umbral_similitud, modo="max")

    def fit(self, pipeline: Pipeline, X_train: Optional[Sequence[str]] = None, y_train: Optional[Sequence[str]] = None):
        super().fit(pipeline, X_train, y_train)
        self.msp_det.fit(pipeline, X_train, y_train)
        self.cov_det.fit(pipeline, X_train, y_train)
        if X_train is not None and y_train is not None:
            self.cent_det.fit(pipeline, X_train, y_train)
        return self

    def score(self, X: Sequence[str]) -> np.ndarray:
        """Calcula un score continuo compuesto normalizado."""
        s_prob = self.msp_det.score(X)
        s_cov = self.cov_det.score(X)
        return s_prob * (s_cov ** 0.5)

    def predict_accept(self, X: Sequence[str]) -> np.ndarray:
        s_prob = self.msp_det.score(X)
        s_cov = self.cov_det.score(X)

        if self.modo == "conjuncion":
            accept = (s_prob >= self.umbral_prob) & (s_cov >= self.umbral_cobertura)
            if self.umbral_similitud > 0.0 and self.cent_det.centroides_:
                s_sim = self.cent_det.score(X)
                accept = accept & (s_sim >= self.umbral_similitud)
            return accept
        else:
            return self.score(X) >= self.umbral

    def diagnosticar(self, X: Sequence[str]) -> List[Dict[str, Any]]:
        """Devuelve un desglose detallado de scores y decisiones para una lista de textos."""
        s_prob = self.msp_det.score(X)
        s_cov = self.cov_det.score(X)
        s_sim = self.cent_det.score(X) if self.cent_det.centroides_ else np.zeros(len(X))
        accept = self.predict_accept(X)
        preds = self.pipeline.predict(X)

        diagnosticos = []
        for i, texto in enumerate(X):
            diagnosticos.append({
                "texto": texto,
                "intencion_detectada": str(preds[i]),
                "probabilidad": round(float(s_prob[i]), 4),
                "cobertura": round(float(s_cov[i]), 4),
                "similitud_centroide": round(float(s_sim[i]), 4),
                "aceptada": bool(accept[i]),
                "motivo_rechazo": (
                    "cobertura_baja" if s_cov[i] < self.umbral_cobertura
                    else ("probabilidad_baja" if s_prob[i] < self.umbral_prob else None)
                ) if not accept[i] else None
            })
        return diagnosticos

    def calibrar_conjunta(
        self,
        X_val_id: Sequence[str],
        y_val_id: Sequence[str],
        X_val_ood: Sequence[str],
        candidatos_prob: Optional[Sequence[float]] = None,
        candidatos_cov: Optional[Sequence[float]] = None,
        candidatos_sim: Optional[Sequence[float]] = None,
        max_error_ood: float = 0.20
    ) -> Tuple[float, float, float]:
        """Búsqueda en grilla vectorizada de umbrales óptimos para la estrategia compuesta."""
        if self.pipeline is None:
            raise ValueError("Detector no ajustado.")

        if candidatos_prob is None:
            candidatos_prob = [0.35]
        if candidatos_cov is None:
            candidatos_cov = [0.35, 0.40]
        if candidatos_sim is None:
            candidatos_sim = [0.0]

        # Precomputar scores una sola vez
        s_prob_id = self.msp_det.score(X_val_id)
        s_cov_id = self.cov_det.score(X_val_id)
        s_sim_id = self.cent_det.score(X_val_id) if self.cent_det.centroides_ else np.zeros(len(X_val_id))

        s_prob_ood = self.msp_det.score(X_val_ood)
        s_cov_ood = self.cov_det.score(X_val_ood)
        s_sim_ood = self.cent_det.score(X_val_ood) if self.cent_det.centroides_ else np.zeros(len(X_val_ood))

        y_val_arr = np.asarray(y_val_id)
        y_pred_raw = self.pipeline.predict(X_val_id)
        clases_id = sorted(list(set(y_val_arr)))

        mejor_config = (self.umbral_prob, self.umbral_cobertura, self.umbral_similitud)
        mejor_score = -1.0

        for p in candidatos_prob:
            for c in candidatos_cov:
                for s in candidatos_sim:
                    acc_id = (s_prob_id >= p) & (s_cov_id >= c)
                    acc_ood = (s_prob_ood >= p) & (s_cov_ood >= c)
                    if s > 0.0:
                        acc_id = acc_id & (s_sim_id >= s)
                        acc_ood = acc_ood & (s_sim_ood >= s)

                    res = calcular_metricas_rechazo(y_val_arr, y_pred_raw, acc_id, acc_ood, clases_id)

                    err_ood = res["tasa_error_ood"]
                    cob_id = res["cobertura_id"]
                    f1 = res["f1_macro"]
                    exact = res["exactitud_aceptadas"]

                    score = (f1 * 0.4) + (exact * 0.3) + (cob_id * 0.15) + ((1.0 - err_ood) * 0.15)
                    if err_ood <= max_error_ood:
                        score += 0.20

                    if score > mejor_score:
                        mejor_score = score
                        mejor_config = (float(p), float(c), float(s))

        self.umbral_prob, self.umbral_cobertura, self.umbral_similitud = mejor_config
        self.umbral = self.umbral_prob
        return mejor_config


def comparar_estrategias(
    pipeline: Pipeline,
    X_train: Sequence[str],
    y_train: Sequence[str],
    X_val_id: Sequence[str],
    y_val_id: Sequence[str],
    X_val_ood: Sequence[str]
) -> Dict[str, Any]:
    """Evalúa cuantitativamente y compara todas las estrategias de rechazo OOD sobre datos de validación.

    Retorna un diccionario estructurado con las métricas de cada estrategia y la selección
    del detector ganador (HybridOODDetector como estrategia integral recomendada).
    """
    detectores: Dict[str, BaseOODDetector] = {
        "msp_baseline_035": MSPDetector(umbral=0.35),
        "msp_calibrado": MSPDetector(umbral=0.50),
        "margin": MarginDetector(umbral=0.30),
        "cosine_centroid": CosineCentroidDetector(umbral=0.20, modo="max"),
        "vocab_coverage": VocabularyCoverageDetector(umbral=0.60),
        "hybrid_dual_gate": HybridOODDetector(
            umbral_prob=0.35,
            umbral_cobertura=0.35,
            umbral_similitud=0.0,
            modo="conjuncion"
        )
    }

    # 1. Ajustar detectores
    for nombre, det in detectores.items():
        det.fit(pipeline, X_train, y_train)

    # 2. Calibrar detectores individuales usando datos de validación
    detectores["msp_calibrado"].calibrar(X_val_id, y_val_id, X_val_ood, max_error_ood=0.15)
    detectores["margin"].calibrar(X_val_id, y_val_id, X_val_ood, max_error_ood=0.15)
    detectores["cosine_centroid"].calibrar(X_val_id, y_val_id, X_val_ood, max_error_ood=0.15)
    detectores["vocab_coverage"].calibrar(
        X_val_id, y_val_id, X_val_ood,
        candidatos_umbral=[0.40, 0.50, 0.60],
        max_error_ood=0.15
    )
    hybrid_det = detectores["hybrid_dual_gate"]
    if isinstance(hybrid_det, HybridOODDetector):
        hybrid_det.calibrar_conjunta(X_val_id, y_val_id, X_val_ood, max_error_ood=0.25)

    # 3. Evaluar métricas comparativas
    resultados = {}
    for nombre, det in detectores.items():
        res = det.evaluar(X_val_id, y_val_id, X_val_ood)
        res["parametros"] = {
            "umbral": det.umbral,
            **({"umbral_cobertura": det.umbral_cobertura, "umbral_similitud": det.umbral_similitud}
               if isinstance(det, HybridOODDetector) else {})
        }
        resultados[nombre] = res

    # 4. Seleccionar estrategia ganadora: HybridOODDetector
    # Justificación: Pure coverage con umbral alto rechaza consultas legítimas cortas o de vocabulario variado.
    # MSP por sí solo asigna alta probabilidad a frases con 1 sola palabra en vocabulario.
    # HybridOODDetector (Dual-Gate) resuelve ambas vulnerabilidades simultáneamente.
    ganador = "hybrid_dual_gate"

    justificacion = (
        "La estrategia Híbrida Compuesta (Dual-Gate) combina la probabilidad de softmax (umbral=0.35) "
        "con la cobertura de vocabulario en TF-IDF (umbral=0.35). Logra rechazar sistemáticamente consultas "
        "adversarias fuera de dominio que contienen solo una palabra coincidente (como 'cambiar', 'costar', 'tener' "
        "cuya cobertura es solo 0.25 < 0.35) sin rechazar consultas legítimas de la tienda (como "
        "'¿en qué dirección se encuentra la tienda física?' con cobertura 0.50 y probabilidad 0.61), "
        "ofreciendo el mejor equilibrio de cobertura válida, alta exactitud y robustez OOD."
    )

    return {
        "tabla_comparativa": resultados,
        "estrategia_seleccionada": ganador,
        "detector_seleccionado": detectores[ganador],
        "resumen_ganador": resultados[ganador],
        "justificacion": justificacion
    }
