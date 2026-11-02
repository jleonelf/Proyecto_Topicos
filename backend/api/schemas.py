"""Esquemas de datos y validaciones con Pydantic para la API REST.

Responsable: Ramiro (Backend)
Propósito:
    Definir los contratos de entrada y salida de los endpoints, garantizando
    validación estricta de tipos, límites de longitud y mensajes de error
    claros en español antes de interactuar con el pipeline de NLP o el modelo.
"""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class ConsultaTextoRequest(BaseModel):
    """Esquema de solicitud para endpoints que reciben texto individual (/predict)."""

    texto: str = Field(
        ...,
        description="Consulta o frase a procesar (entre 3 y 500 caracteres).",
        examples=["¿Tienen jeans negros en talla 32?"],
    )

    @field_validator("texto")
    @classmethod
    def validar_texto(cls, valor: str) -> str:
        """Valida que el texto no esté vacío y cumpla los límites de caracteres."""
        limpio = valor.strip()
        if not limpio or len(limpio) < 3:
            raise ValueError("El texto debe contener al menos 3 caracteres no vacíos.")
        if len(limpio) > 500:
            raise ValueError("El texto excede el límite máximo permitido de 500 caracteres.")
        return limpio


class ChatRequest(BaseModel):
    """Esquema de solicitud para el endpoint interactivo del chatbot (/chat)."""

    texto: str = Field(
        ...,
        description="Mensaje del usuario.",
        examples=["Hola, ¿qué precio tiene la chaqueta de cuero?"],
    )
    rol: Literal["cliente", "admin"] = Field(
        default="cliente",
        description="Rol del emisor: 'cliente' para consultas de tienda o 'admin' para reportes.",
        examples=["cliente"],
    )

    @field_validator("texto")
    @classmethod
    def validar_texto(cls, valor: str) -> str:
        limpio = valor.strip()
        if not limpio or len(limpio) < 3:
            raise ValueError("El texto debe contener al menos 3 caracteres no vacíos.")
        if len(limpio) > 500:
            raise ValueError("El texto excede el límite máximo permitido de 500 caracteres.")
        return limpio


class TopPrediccion(BaseModel):
    """Estructura de una predicción candidata con su probabilidad."""

    intencion: str = Field(..., description="Nombre de la intención identificada.")
    probabilidad: float = Field(..., description="Probabilidad asignada por el modelo (0.0 a 1.0).")


class PredictResponse(BaseModel):
    """Esquema de respuesta para el endpoint /predict."""

    intencion: str = Field(..., description="Intención ganadora predicha por el modelo.")
    probabilidad: float = Field(..., description="Confianza de la predicción principal.")
    top3: List[TopPrediccion] = Field(
        default_factory=list,
        description="Las tres intenciones con mayor probabilidad.",
    )


class ChatResponse(BaseModel):
    """Esquema de respuesta integral para el endpoint /chat."""

    intencion: str = Field(..., description="Intención detectada o 'desconocida'.")
    probabilidad: float = Field(..., description="Nivel de confianza de la intención.")
    entidades: Dict[str, Any] = Field(
        default_factory=dict,
        description="Entidades detectadas en la consulta (talla, color, producto, etc.).",
    )
    respuesta: str = Field(..., description="Respuesta final textual generada para el usuario.")
    pasos: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Etapas del preprocesamiento de NLP paso a paso (para visualización en frontend).",
    )
    # Agregados para que el frontend muestre el resultado real del modelo (Fernando)
    intencion_detectada: Optional[str] = Field(
        default=None,
        description="Intención más probable según el modelo, aunque no supere el umbral de confianza.",
    )
    top3: List[TopPrediccion] = Field(
        default_factory=list,
        description="Las tres intenciones con mayor probabilidad según el modelo.",
    )


class HealthResponse(BaseModel):
    """Esquema de respuesta para el diagnóstico de salud del servicio (/health)."""

    estado: str = Field(..., description="Estado general de la API ('activo').")
    version: str = Field(..., description="Versión de la API.")
    modelo_cargado: bool = Field(
        ...,
        description="Indica si el artefacto del modelo ML está disponible y listo para inferir.",
    )
    tienda_cargada: bool = Field(
        ...,
        description="Indica si la base de datos de la tienda está disponible para consultas.",
    )
    detalles: Dict[str, Any] = Field(
        default_factory=dict,
        description="Rutas y metadatos del estado del sistema.",
    )


class ErrorDetalleResponse(BaseModel):
    """Esquema estandarizado para respuestas de error con mensajes en español."""

    error: str = Field(..., description="Categoría o tipo de error.")
    detalle: str = Field(..., description="Descripción clara y legible de la causa del fallo.")


class PredictLoteItemResponse(BaseModel):
    """Predicción para un elemento individual dentro de un lote."""

    texto: str = Field(..., description="Texto analizado.")
    intencion: str = Field(..., description="Intención detectada.")
    probabilidad: float = Field(..., description="Nivel de confianza de la predicción.")


class PredictLoteResponse(BaseModel):
    """Respuesta para el endpoint de predicción masiva en lote (/predict/lote)."""

    total: int = Field(..., description="Cantidad total de textos procesados.")
    predicciones: List[PredictLoteItemResponse] = Field(
        ..., description="Lista de predicciones obtenidas."
    )


class PredictLoteJsonRequest(BaseModel):
    """Esquema para enviar lista de textos en formato JSON."""

    textos: List[str] = Field(
        ...,
        description="Lista de textos a predecir (mínimo 1, máximo 100).",
        examples=[["¿Tienen jeans?", "Horarios de atención", "Precios de camisas"]],
    )

    @field_validator("textos")
    @classmethod
    def validar_textos(cls, textos: List[str]) -> List[str]:
        if not textos:
            raise ValueError("La lista de textos no puede estar vacía.")
        if len(textos) > 100:
            raise ValueError("El lote no puede exceder los 100 textos por solicitud.")
        limpios = [t.strip() for t in textos if t and t.strip()]
        if not limpios:
            raise ValueError("Ninguno de los textos proporcionados es válido.")
        return limpios


class MetricsResponse(BaseModel):
    """Esquema de respuesta para el panel de métricas del modelo (/metrics)."""

    modelo_activo: str = Field(..., description="Nombre del modelo en producción.")
    accuracy: float = Field(..., description="Exactitud global del modelo.")
    f1_macro: float = Field(..., description="F1-Score promedio macro.")
    f1_por_clase: Dict[str, float] = Field(
        default_factory=dict, description="F1-Score desglosado por intención."
    )
    matriz_confusion: Dict[str, Any] = Field(
        default_factory=dict, description="Matriz de confusión calculada con etiquetas."
    )
    comparativa_modelos: Optional[Dict[str, Any]] = Field(
        default=None, description="Comparación entre modelos evaluados (ej. Logística vs Naive Bayes)."
    )


class TiendaImportarResponse(BaseModel):
    """Resumen de lo importado para la tienda (/tienda/importar)."""

    estado: str = Field(..., description="Resultado de la importación ('exitoso' o 'error').")
    mensaje: str = Field(..., description="Mensaje explicativo del proceso.")
    productos_importados: int = Field(..., description="Total de productos registrados.")
    ventas_importadas: int = Field(..., description="Total de registros de venta importados.")


class ReporteItem(BaseModel):
    """Elemento genérico dentro de un reporte."""

    concepto: str = Field(..., description="Etiqueta, categoría o producto.")
    cantidad: float = Field(..., description="Valor numérico, unidades o total facturado.")
    detalles: Optional[Dict[str, Any]] = Field(default=None, description="Datos secundarios.")


class ReporteResponse(BaseModel):
    """Respuesta general para los reportes administrativos (/reportes/{tipo})."""

    tipo_reporte: str = Field(..., description="Tipo de reporte consultado.")
    rango: Optional[str] = Field(default=None, description="Período o filtro aplicado.")
    resumen: Dict[str, Any] = Field(..., description="Totales o agregaciones clave.")
    datos: List[Dict[str, Any]] = Field(
        default_factory=list, description="Lista detallada de datos del reporte."
    )

