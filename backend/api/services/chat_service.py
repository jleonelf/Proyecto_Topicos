"""Servicio de inferencia y generación de respuestas para el chat y predicción.

Responsable: Ramiro (Backend)
Funcionalidades:
    - Carga en memoria y caché del modelo serializado (artifacts/modelo.joblib).
    - Mecanismo de contingencia (fallback heurístico) para desarrollo desacoplado.
    - Extracción de probabilidades y Top 3 de intenciones.
    - Aplicación del umbral de confianza (si prob < umbral -> "no entendí").
    - Generación de respuestas mediante plantillas dinámicas según intención y entidades.
    - Desglose de pasos de preprocesamiento para visualización en el frontend.
"""

from pathlib import Path
import re
import unicodedata
from typing import Any, Dict, List, Optional, Tuple
import joblib

from src.config import config
from src.nlp.entidades import extraer_entidades
from src.nlp.pipeline import preprocesar_pasos  # fases 1-4 reales (Fernando)
from api.services.respuestas_datos import responder_con_datos  # respuestas con datos de la base (Fernando)

RAIZ_PROYECTO = Path(__file__).resolve().parent.parent.parent

# Cache global del modelo en memoria
_MODELO_CACHE: Optional[Any] = None
_MODELO_MTIME: Optional[float] = None

# Las 13 intenciones acordadas por el equipo
INTENCIONES_VALIDAS: List[str] = [
    "saludo",
    "despedida",
    "consultar_stock",
    "consultar_precio",
    "consultar_tallas",
    "envios",
    "devoluciones",
    "horarios_ubicacion",
    "metodos_pago",
    "reporte_ventas",
    "productos_mas_vendidos",
    "stock_bajo",
    "ventas_por_categoria",
]

# Reglas heurísticas de respaldo para cuando modelo.joblib aún no existe
HEURISTICAS_INTENCIONES: Dict[str, List[str]] = {
    "saludo": ["hola", "buen dia", "buenos dias", "buenas tardes", "buenas noches", "que tal", "saludos"],
    "despedida": ["adios", "chau", "hasta luego", "muchas gracias", "eso era todo", "gracias"],
    "consultar_stock": ["stock", "tienen", "hay", "queda", "les queda", "disponible", "disponibilidad"],
    "consultar_precio": ["precio", "cuesta", "cuanto", "vale", "costo", "valor"],
    "consultar_tallas": ["talla", "tallas", "medida", "medidas", "grande", "mediana", "chica", "tabla"],
    "envios": ["envio", "envios", "delivery", "domicilio", "enviar", "paqueteria", "provincia", "llega"],
    "devoluciones": ["cambio", "cambiar", "devolucion", "devolver", "reembolso", "garantia"],
    "horarios_ubicacion": ["horario", "hora", "abren", "cierran", "donde", "ubicacion", "direccion", "sucursal"],
    "metodos_pago": ["pago", "pagar", "tarjeta", "efectivo", "qr", "transferencia", "credito", "debito"],
    "reporte_ventas": ["reporte de ventas", "balance", "total vendido", "cuanto se vendio", "informe de ventas"],
    "productos_mas_vendidos": ["mas vendido", "mas vendidos", "top ventas", "articulos mas vendidos", "mayor demanda"],
    "stock_bajo": ["stock bajo", "se estan acabando", "stock critico", "agotandose", "reposicion urgente"],
    "ventas_por_categoria": ["ventas por categoria", "ventas de jeans", "desglose por seccion", "por departamento"],
}


def _limpiar_texto(texto: str) -> str:
    """Normaliza texto eliminando acentos y mayúsculas."""
    nfkd = unicodedata.normalize("NFKD", texto.lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def obtener_ruta_modelo() -> Path:
    """Resuelve la ruta absoluta al modelo guardado."""
    rel = config.get("rutas", {}).get("modelo_guardado", "artifacts/modelo.joblib")
    return RAIZ_PROYECTO / rel


def cargar_modelo() -> Optional[Any]:
    """Carga el modelo serializado desde disco con caché y recarga automática."""
    global _MODELO_CACHE, _MODELO_MTIME
    ruta = obtener_ruta_modelo()

    if not ruta.is_file():
        return None

    try:
        mtime_actual = ruta.stat().st_mtime
        if _MODELO_CACHE is None or _MODELO_MTIME != mtime_actual:
            _MODELO_CACHE = joblib.load(ruta)
            _MODELO_MTIME = mtime_actual
        return _MODELO_CACHE
    except Exception:
        return None


def _predecir_heuristico(texto: str) -> Tuple[str, float, List[Dict[str, Any]]]:
    """Clasificador de contingencia cuando modelo.joblib aún no ha sido entrenado."""
    texto_norm = _limpiar_texto(texto)
    puntajes: Dict[str, int] = {intencion: 0 for intencion in INTENCIONES_VALIDAS}

    for intencion, palabras_clave in HEURISTICAS_INTENCIONES.items():
        for clave in palabras_clave:
            if re.search(r"\b" + re.escape(clave) + r"\b", texto_norm):
                # Palabras compuestas tienen mayor peso discriminante
                puntajes[intencion] += 2 if " " in clave else 1

    max_puntos = max(puntajes.values()) if puntajes else 0

    if max_puntos > 0:
        # Normalizar a probabilidades relativas
        total = sum(puntajes.values())
        lista_ordenada = sorted(
            [{"intencion": k, "probabilidad": round(v / total, 4)} for k, v in puntajes.items() if v > 0],
            key=lambda x: x["probabilidad"],
            reverse=True,
        )
        ganador = lista_ordenada[0]
        # Asegurar al menos top 3
        while len(lista_ordenada) < 3:
            otra = next(i for i in INTENCIONES_VALIDAS if i not in [x["intencion"] for x in lista_ordenada])
            lista_ordenada.append({"intencion": otra, "probabilidad": 0.01})

        return (ganador["intencion"], ganador["probabilidad"], lista_ordenada[:3])

    # Si no hubo coincidencia alguna, devolver baja confianza
    return (
        "consultar_stock",
        0.35,
        [
            {"intencion": "consultar_stock", "probabilidad": 0.35},
            {"intencion": "consultar_precio", "probabilidad": 0.25},
            {"intencion": "saludo", "probabilidad": 0.15},
        ],
    )


def predecir_intencion(texto: str) -> Tuple[str, float, List[Dict[str, Any]]]:
    """Determina la intención de una consulta y el Top 3 de probabilidades.

    Utiliza el modelo entrenado real (artifacts/modelo.joblib). Si no está disponible,
    recurre a las heurísticas de contingencia para no bloquear el desarrollo.
    """
    modelo = cargar_modelo()

    if modelo is not None and hasattr(modelo, "predict_proba"):
        try:
            probabilidades = modelo.predict_proba([texto])[0]
            clases = list(modelo.classes_)
            
            pares = list(zip(clases, probabilidades))
            pares_ordenados = sorted(pares, key=lambda p: p[1], reverse=True)

            intencion_ganadora = pares_ordenados[0][0]
            probabilidad_ganadora = float(pares_ordenados[0][1])

            top3 = [
                {"intencion": str(par[0]), "probabilidad": round(float(par[1]), 4)}
                for par in pares_ordenados[:3]
            ]
            return (intencion_ganadora, round(probabilidad_ganadora, 4), top3)
        except Exception:
            pass

    return _predecir_heuristico(texto)


def obtener_pasos_preprocesamiento(texto: str) -> Dict[str, Any]:
    """Genera las etapas paso a paso del texto para visualización en el frontend."""
    # Regla de oro del plan: se usan las fases 1-4 reales (src/nlp/pipeline.py),
    # las mismas que van dentro de modelo.joblib, en lugar de reimplementarlas.
    try:
        return preprocesar_pasos(texto)
    except Exception:
        pass  # si spaCy no está disponible, se usa la versión simplificada de abajo

    # Paso 1: Normalización básica
    normalizado = _limpiar_texto(texto)
    # Paso 2: Tokenización
    tokens = re.findall(r"\b[a-z0-9]+\b", normalizado)
    # Paso 3: Eliminación de stopwords conservando palabras clave de sentido
    stopwords_comunes = {
        "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "a",
        "en", "para", "por", "con", "y", "o", "u", "es", "son", "un", "me", "que",
        "quisiera", "hola", "buenas", "porfa"
    }
    # Respetar exclusión de 'no', 'sin', 'mas' acordada en config.yaml
    sin_stopwords = [t for t in tokens if t not in stopwords_comunes]

    # Paso 4: Forma simplificada (lemas o raíces)
    lemas = [t[:-1] if t.endswith("s") and len(t) > 3 else t for t in sin_stopwords]

    return {
        "original": texto,
        "normalizado": normalizado,
        "tokens": tokens,
        "sin_stopwords": sin_stopwords,
        "lemas_o_raices": lemas,
    }


def generar_respuesta_chat(
    intencion: str,
    probabilidad: float,
    entidades: Dict[str, Optional[str]],
    rol: str = "cliente",
) -> Tuple[str, str]:
    """Aplica el umbral de confianza y genera una respuesta contextual mediante plantillas.

    Returns:
        Tupla con (intencion_final, texto_respuesta).
    """
    umbral = float(config.get("api", {}).get("umbral_confianza", 0.60))

    # Regla del umbral de confianza acordada en el plan
    if probabilidad < umbral:
        mensaje_duda = (
            f"No estoy seguro de haber entendido tu consulta (confianza: {probabilidad * 100:.1f}%). "
            "¿Podrías reformularla indicando si deseas consultar stock, precios, tallas, envíos o reportes?"
        )
        return ("desconocido", mensaje_duda)

    # Primero se intenta responder con los datos reales importados (stock, precios,
    # horarios, reportes...). Si la base no tiene esos datos, siguen las plantillas.
    respuesta_real = responder_con_datos(intencion, entidades)
    if respuesta_real:
        return (intencion, respuesta_real)

    talla = entidades.get("talla")
    color = entidades.get("color")
    producto = entidades.get("producto") or "la prenda"
    fecha = entidades.get("fecha") or "este periodo"

    # Plantillas contextuales para las 13 intenciones
    if intencion == "saludo":
        return ("saludo", "¡Hola! Bienvenido a nuestra tienda de ropa. ¿En qué te puedo colaborar hoy?")

    if intencion == "despedida":
        return ("despedida", "¡Muchas gracias por comunicarte con nosotros! Que tengas un excelente día.")

    if intencion == "consultar_stock":
        if talla and color:
            return ("consultar_stock", f"Sí, contamos con stock disponible de {producto} en color {color} y talla {talla}.")
        elif talla:
            return ("consultar_stock", f"Sí, tenemos {producto} disponible en talla {talla} en varios colores.")
        elif color:
            return ("consultar_stock", f"Sí, tenemos {producto} en color {color}. ¿Qué talla necesitas?")
        else:
            return ("consultar_stock", f"Tenemos amplio surtido de {producto}. ¿Qué talla o color estás buscando?")

    if intencion == "consultar_precio":
        if producto and producto != "la prenda":
            return ("consultar_precio", f"El precio de {producto} varía según el modelo. Por ejemplo, contamos con modelos desde 90 Bs hasta 180 Bs. ¿Deseas consultar un color o talla?")
        return ("consultar_precio", "Nuestros precios son muy accesibles: poleras desde 60 Bs, jeans desde 120 Bs y chaquetas desde 190 Bs. ¿Qué prenda te interesa?")

    if intencion == "consultar_tallas":
        return ("consultar_tallas", "Manejamos tallas estándar desde la XS hasta la XXL y pantalones desde la talla 28 hasta la 44. ¿Te gustaría la tabla de medidas?")

    if intencion == "envios":
        return ("envios", "Realizamos envíos a todo el país. La entrega demora entre 24 y 48 horas hábiles, y el envío es gratis por compras mayores a 200 Bs.")

    if intencion == "devoluciones":
        return ("devoluciones", "Tienes hasta 15 días calendario para solicitar cambio o devolución, presentando la prenda con sus etiquetas originales.")

    if intencion == "horarios_ubicacion":
        return ("horarios_ubicacion", "Nuestra tienda central atiende de lunes a sábado de 9:00 a 20:00 y domingos de 10:00 a 16:00 en Av. Principal #123.")

    if intencion == "metodos_pago":
        return ("metodos_pago", "Aceptamos pagos en efectivo, transferencias bancarias, cobro QR Simple y tarjetas de débito/crédito (Visa y Mastercard).")

    # Intenciones administrativas
    if intencion == "reporte_ventas":
        return ("reporte_ventas", f"Reporte administrativo: Para {fecha} se registraron 134 transacciones con un total facturado de 16,820 Bs.")

    if intencion == "productos_mas_vendidos":
        return ("productos_mas_vendidos", f"Artículos más vendidos en {fecha}: 1. Jeans Clásicos (52 unid.), 2. Chaquetas de Cuero (38 unid.), 3. Poleras Básicas (35 unid.).")

    if intencion == "stock_bajo":
        return ("stock_bajo", "Alerta de inventario: Hay 3 referencias con stock crítico (< 5 unidades): Jeans negros 32 (2 unid.), Polera blanca M (3 unid.) y Vestido rojo S (1 unid.).")

    if intencion == "ventas_por_categoria":
        return ("ventas_por_categoria", f"Distribución de ventas por categoría en {fecha}: Pantalones 45%, Abrigos 25%, Camisetas 20%, Calzado 10%.")

    return (intencion, "Consulta recibida y procesada correctamente.")
