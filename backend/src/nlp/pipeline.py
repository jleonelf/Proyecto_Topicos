"""Unión de las fases 1 a 4 del preprocesamiento.

Responsable: Fernando.

    TextPreprocessor        transformer de scikit-learn que va DENTRO del modelo
                            guardado (artifacts/modelo.joblib), como primer paso:
                            preprocesamiento -> vectorizador -> modelo
    preprocesar_pasos(t)    devuelve cada paso intermedio de un texto, para que el
                            frontend muestre cómo se procesó la consulta

Recorrido de un texto:

    "¿Cuánto cuesta la chaqueta de cuero, porfa?"
      1. normalizar        "cuanto cuesta la chaqueta de cuero porfa"
      2. tokenizar         [cuanto, cuesta, la, chaqueta, de, cuero, porfa]
      4. lematizar         [cuanto, costar, el, chaqueta, de, cuero, porfa]
      3. quitar stop words [cuanto, costar, chaqueta, cuero]   <- texto final

La fase 4 se aplica ANTES que la 3 (sobre la frase completa) porque spaCy
necesita el contexto para lematizar bien ("cuesta" verbo -> "costar"). Después
se descartan los lemas cuyas palabras originales son stop words, así la lista
de stop words se compara con las palabras tal como las escribió el usuario.

Regla de oro del plan: el backend carga modelo.joblib y nunca reimplementa
estos pasos; el mismo objeto que se usó al entrenar procesa cada consulta.
"""

from typing import Any, Dict, Iterable, List

from sklearn.base import BaseEstimator, TransformerMixin

from src.nlp.lematizacion import lematizar, stemmizar
from src.nlp.normalizacion import normalizar
from src.nlp.stopwords import LISTAS, lista_stopwords
from src.nlp.tokenizacion import tokenizar

MODOS = ("lema", "stem")


class TextPreprocessor(BaseEstimator, TransformerMixin):
    """Convierte textos crudos en textos preprocesados (fases 1 a 4).

    Parámetros (vienen de la sección nlp de src/config.yaml):
        modo               "lema" (spaCy) o "stem" (Snowball)
        stopwords_extra    palabras que se agregan a la lista de stop words
        stopwords_exclude  palabras que se quitan de la lista de stop words
        lista_stopwords    "ajustada" (dominio) o "spacy" (sin ajustes, para comparar)

    No aprende nada de los datos (fit no hace nada), así que usarlo dentro de
    la validación cruzada no filtra información entre particiones.
    """

    def __init__(
        self,
        modo: str = "lema",
        stopwords_extra: Iterable[str] = (),
        stopwords_exclude: Iterable[str] = (),
        lista_stopwords: str = "ajustada",
    ):
        # scikit-learn exige guardar los parámetros tal cual llegan (para clonar
        # el objeto en GridSearchCV); la validación se hace en fit.
        self.modo = modo
        self.stopwords_extra = stopwords_extra
        self.stopwords_exclude = stopwords_exclude
        self.lista_stopwords = lista_stopwords

    def fit(self, X, y=None):
        """Solo valida la configuración; no hay nada que aprender."""
        if self.modo not in MODOS:
            raise ValueError(f"modo debe ser uno de {MODOS}, no '{self.modo}'")
        if self.lista_stopwords not in LISTAS:
            raise ValueError(f"lista_stopwords debe ser una de {LISTAS}, no '{self.lista_stopwords}'")
        return self

    def transform(self, X) -> List[str]:
        """Devuelve cada texto como una cadena de tokens finales separados por espacio.

        El vectorizador TF-IDF (fase 5) recibe esta salida.
        """
        return [" ".join(self.pasos(texto)["final"]) for texto in X]

    def pasos(self, texto: Any) -> Dict[str, Any]:
        """Aplica las fases 1 a 4 a un texto y devuelve cada resultado intermedio."""
        texto = texto if isinstance(texto, str) else ""  # nulos o números -> texto vacío

        normalizado = normalizar(texto)  # fase 1
        tokens = tokenizar(normalizado)  # fase 2

        # Fase 4 sobre la frase completa: un lema/raíz por cada token
        reducidos = lematizar(tokens) if self.modo == "lema" else stemmizar(tokens)

        # Fase 3: se decide con la palabra original si es stop word
        stop = lista_stopwords(
            self.lista_stopwords, tuple(self.stopwords_extra), tuple(self.stopwords_exclude)
        )
        eliminadas = [t for t in tokens if t in stop]
        conservadas = [(t, r) for t, r in zip(tokens, reducidos) if t not in stop]

        return {
            "original": texto,
            "normalizado": normalizado,
            "tokens": tokens,
            "stopwords_eliminadas": eliminadas,
            "sin_stopwords": [t for t, _ in conservadas],
            "lemas_o_raices": [r for _, r in conservadas],
            "modo": self.modo,
            "final": [r for _, r in conservadas],  # lo que recibe TF-IDF
        }


def crear_preprocesador(config: Dict[str, Any]) -> TextPreprocessor:
    """Construye el TextPreprocessor con la sección nlp de config.yaml."""
    nlp_cfg = config.get("nlp", {})
    return TextPreprocessor(
        modo=nlp_cfg.get("modo", "lema"),
        stopwords_extra=nlp_cfg.get("stopwords_extra") or (),
        stopwords_exclude=nlp_cfg.get("stopwords_exclude") or (),
        lista_stopwords=nlp_cfg.get("lista_stopwords", "ajustada"),
    )


def preprocesar_pasos(texto: str, config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Cada paso del preprocesamiento de un texto, para la vista del frontend.

    Sin config usa src/config.yaml, que es la misma configuración con la que se
    entrena el modelo.

    Ejemplo:
        >>> preprocesar_pasos("¿Cuánto cuesta la chaqueta, porfa?")["final"]
        ['cuanto', 'costar', 'chaqueta']
    """
    if config is None:
        from src.config import config as config_global  # se importa aquí para no leer el YAML al importar el módulo

        config = config_global
    return crear_preprocesador(config).pasos(texto)
