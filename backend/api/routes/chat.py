"""Rutas de la API para clasificación de intenciones y chat interactivo.

Responsable: Ramiro (Backend)
Endpoints:
    - POST /predict: Clasifica una frase individual retornando la intención ganadora,
      su probabilidad y las 3 intenciones más probables.
    - POST /chat: Flujo completo del asistente: predicción de intención, control de
      umbral de confianza (< 0.60 -> "no entendí"), extracción de entidades,
      generación de respuesta contextual y pasos del preprocesamiento para el frontend.
"""

from fastapi import APIRouter, status
from api.schemas import (
    ConsultaTextoRequest,
    PredictResponse,
    TopPrediccion,
    ChatRequest,
    ChatResponse,
)
from src.nlp.entidades import extraer_entidades
from api.services.chat_service import (
    predecir_intencion,
    generar_respuesta_chat,
    obtener_pasos_preprocesamiento,
)

router = APIRouter(tags=["Chat y Predicciones"])


@router.post(
    "/predict",
    response_model=PredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Clasificar intención de un texto",
)
async def predict(solicitud: ConsultaTextoRequest) -> PredictResponse:
    """Clasifica la intención del texto ingresado y retorna el Top 3 de probabilidades."""
    intencion, probabilidad, top3_raw = predecir_intencion(solicitud.texto)

    top3 = [
        TopPrediccion(intencion=item["intencion"], probabilidad=item["probabilidad"])
        for item in top3_raw
    ]

    return PredictResponse(
        intencion=intencion,
        probabilidad=probabilidad,
        top3=top3,
    )


@router.post(
    "/chat",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
    summary="Interacción conversacional completa con el asistente",
)
async def chat(solicitud: ChatRequest) -> ChatResponse:
    """Procesa una consulta de chat combinando clasificación, entidades y plantillas."""
    # 1. Inferencia de intención y confianza
    intencion, probabilidad, _ = predecir_intencion(solicitud.texto)

    # 2. Extracción de entidades (talla, color, producto, fecha)
    entidades = extraer_entidades(solicitud.texto)

    # 3. Aplicación del umbral de confianza y respuesta contextual
    intencion_final, respuesta = generar_respuesta_chat(
        intencion=intencion,
        probabilidad=probabilidad,
        entidades=entidades,
        rol=solicitud.rol,
    )

    # 4. Desglose pedagógico de los pasos de preprocesamiento para el frontend
    pasos = obtener_pasos_preprocesamiento(solicitud.texto)

    return ChatResponse(
        intencion=intencion_final,
        probabilidad=probabilidad,
        entidades=entidades,
        respuesta=respuesta,
        pasos=pasos,
    )
