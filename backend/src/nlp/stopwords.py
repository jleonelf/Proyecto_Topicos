"""Fase 3: Eliminación de stop words.

Responsable: Fernando.
Función principal: quitar_stopwords(tokens) -> list[str]

Lista base: stop words en español de spaCy (521 palabras, 462 al quitar tildes,
porque la normalización de la fase 1 entrega el texto sin tildes y las palabras
de la lista se comparan en esa misma forma).

Por qué se ajusta la lista: spaCy está pensada para texto general y borra
palabras que en una tienda de ropa deciden la intención. Sin ajustes,
"¿cuánto cuesta?" quedaría en "cuesta" y "stock bajo" en "stock".

Palabras que se QUITAN de la lista (se conservan en el texto):
    - Negación y cantidad: no, sin, mas, menos, poco, nada, nunca.
      Cambian el sentido: "sin stock", "no tienen", "algo más barato".
    - Interrogativas: cuanto(s), cuanta(s) -> consultar_precio;
      donde, cuando -> horarios_ubicacion; como -> metodos_pago y envios;
      cual, cuales -> consultar_tallas.
    - Disponibilidad: hay, tiene, tienen -> consultar_stock.
    - Saludo y despedida: buen, buena(s), bueno(s), dias, hasta, luego
      ("buenos días", "hasta luego").
    - Reportes de administración: hoy, ultimo(s), ultima, mayor, bajo, total
      ("ventas de hoy", "último mes", "mayor demanda", "stock bajo",
      "total vendido").

Palabras que se AGREGAN a la lista: muletillas de chat que no aportan a la
intención: porfa, porfis, plis, xfa, oye, disculpa, favor ("por favor").

Las palabras "hola" y "gracias" NO son stop words: son la señal principal de
saludo y despedida.

Los ajustes extra de src/config.yaml (nlp.stopwords_extra y
nlp.stopwords_exclude) se aplican encima de estos, para modificar la lista en
vivo sin tocar el código.
"""

from functools import lru_cache
from typing import Iterable, List

from src.nlp.normalizacion import normalizar

LISTAS = ("ajustada", "spacy")

PALABRAS_CONSERVADAS = frozenset({
    # Negación y cantidad
    "no", "sin", "mas", "menos", "poco", "nada", "nunca",
    # Interrogativas
    "cuanto", "cuanta", "cuantos", "cuantas", "donde", "cuando", "como", "cual", "cuales",
    # Disponibilidad
    "hay", "tiene", "tienen",
    # Saludo y despedida
    "buen", "buena", "buenas", "bueno", "buenos", "dias", "hasta", "luego",
    # Reportes de administración
    "hoy", "ultimo", "ultima", "ultimos", "mayor", "bajo", "total",
})

STOPWORDS_AGREGADAS = frozenset({"porfa", "porfis", "plis", "xfa", "oye", "disculpa", "favor"})


@lru_cache(maxsize=None)
def lista_stopwords(lista: str = "ajustada", extra: tuple = (), excluir: tuple = ()) -> frozenset:
    """Devuelve el conjunto de stop words, normalizado igual que los tokens.

    lista="spacy" es la lista de spaCy sin cambios (sirve para comparar);
    lista="ajustada" aplica los ajustes del dominio. En ambos casos se suman
    las palabras de extra y se quitan las de excluir.
    """
    if lista not in LISTAS:
        raise ValueError(f"lista debe ser una de {LISTAS}, no '{lista}'")

    from spacy.lang.es.stop_words import STOP_WORDS

    palabras = {normalizar(p) for p in STOP_WORDS}
    if lista == "ajustada":
        palabras -= PALABRAS_CONSERVADAS
        palabras |= STOPWORDS_AGREGADAS
    palabras |= {normalizar(p) for p in extra}
    palabras -= {normalizar(p) for p in excluir}
    palabras.discard("")
    return frozenset(palabras)


def quitar_stopwords(
    tokens: List[str],
    extra: Iterable[str] = (),
    excluir: Iterable[str] = (),
    lista: str = "ajustada",
) -> List[str]:
    """Elimina las stop words de una lista de tokens ya normalizados.

    Ejemplo:
        >>> quitar_stopwords(["cuanto", "cuesta", "la", "chaqueta", "de", "cuero", "porfa"])
        ['cuanto', 'cuesta', 'chaqueta', 'cuero']
    """
    stop = lista_stopwords(lista, tuple(extra), tuple(excluir))
    return [t for t in tokens if t not in stop]
