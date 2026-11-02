"""Rutas de la API para métricas del modelo, reportes administrativos y predicción en lote.

Responsable: Ramiro (Backend)
Endpoints:
    - GET /metrics: Retorna métricas de evaluación del modelo (Accuracy, F1-macro, F1 por clase y matriz de confusión).
    - GET /reportes/{tipo}: Genera agregaciones para el panel administrativo (ventas, mas_vendidos, stock_bajo, categorias).
    - POST /predict/lote: Clasificación en lote mediante JSON o carga de archivo .txt/.csv.
    - POST /tienda/importar: Carga e importación de datos de catálogo y ventas.
"""

from typing import List, Optional
from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse

from api.schemas import (
    MetricsResponse,
    ReporteResponse,
    PredictLoteResponse,
    PredictLoteItemResponse,
    PredictLoteJsonRequest,
    TiendaImportarResponse,
)
from api.services.reportes_service import (
    obtener_metricas_modelo,
    obtener_reporte,
    predecir_lote_textos,
    TIPOS_REPORTES_VALIDOS,
)

router = APIRouter(tags=["Reportes y Administración"])


# ------------------------------------------------------------------------------
# Métricas de Modelos
# ------------------------------------------------------------------------------
@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Métricas de evaluación del modelo y comparación",
)
async def get_metrics() -> MetricsResponse:
    """Retorna las métricas cuantitativas del modelo en producción y su comparación."""
    datos = obtener_metricas_modelo()
    return MetricsResponse(
        modelo_activo=datos.get("modelo_activo", "Desconocido"),
        accuracy=float(datos.get("accuracy", 0.0)),
        f1_macro=float(datos.get("f1_macro", 0.0)),
        f1_por_clase=datos.get("f1_por_clase", {}),
        matriz_confusion=datos.get("matriz_confusion", {}),
        comparativa_modelos=datos.get("comparativa_modelos"),
    )


# ------------------------------------------------------------------------------
# Reportes Administrativos
# ------------------------------------------------------------------------------
@router.get(
    "/reportes/{tipo}",
    response_model=ReporteResponse,
    summary="Consultar reportes administrativos de la tienda",
)
async def get_reporte(
    tipo: str,
    rango: Optional[str] = Query(
        default=None,
        description="Filtro temporal (ej. 'esta semana', 'octubre', '2026-10-01:2026-10-31').",
    ),
) -> ReporteResponse:
    """Genera datos estructurados para las vistas administrativas del frontend."""
    try:
        resultado = obtener_reporte(tipo=tipo, rango=rango)
        return ReporteResponse(
            tipo_reporte=resultado["tipo_reporte"],
            rango=resultado.get("rango"),
            resumen=resultado["resumen"],
            datos=resultado["datos"],
        )
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Tipo de reporte inválido", "detalle": str(e)},
        )


# ------------------------------------------------------------------------------
# Predicción en Lote
# ------------------------------------------------------------------------------
@router.post(
    "/predict/lote",
    response_model=PredictLoteResponse,
    summary="Predicción masiva mediante lista JSON",
)
async def predict_lote(solicitud: PredictLoteJsonRequest) -> PredictLoteResponse:
    """Recibe un arreglo de frases y devuelve la intención y probabilidad de cada una."""
    predicciones_raw = predecir_lote_textos(solicitud.textos)
    predicciones = [
        PredictLoteItemResponse(
            texto=item["texto"],
            intencion=item["intencion"],
            probabilidad=item["probabilidad"],
        )
        for item in predicciones_raw
    ]
    return PredictLoteResponse(
        total=len(predicciones),
        predicciones=predicciones,
    )


@router.post(
    "/predict/lote/archivo",
    response_model=PredictLoteResponse,
    summary="Predicción masiva subiendo archivo .txt o .csv",
)
async def predict_lote_archivo(
    archivo: UploadFile = File(..., description="Archivo de texto plano o CSV con una frase por línea.")
) -> PredictLoteResponse:
    """Procesa un archivo de texto o CSV y clasifica todas las consultas contenidas."""
    nombre = archivo.filename or ""
    if not (nombre.endswith(".txt") or nombre.endswith(".csv")):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Formato de archivo inválido",
                "detalle": "El archivo para predicción en lote debe ser de extensión .txt o .csv.",
            },
        )

    contenido = await archivo.read()
    lineas = contenido.decode("utf-8", errors="ignore").splitlines()
    textos = [linea.strip() for linea in lineas if linea.strip() and not linea.startswith("#")]

    if not textos:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Archivo vacío o sin datos",
                "detalle": "El archivo proporcionado no contiene frases válidas para procesar.",
            },
        )

    predicciones_raw = predecir_lote_textos(textos[:100])  # Límite seguro de 100
    predicciones = [
        PredictLoteItemResponse(
            texto=item["texto"],
            intencion=item["intencion"],
            probabilidad=item["probabilidad"],
        )
        for item in predicciones_raw
    ]

    return PredictLoteResponse(
        total=len(predicciones),
        predicciones=predicciones,
    )


# ------------------------------------------------------------------------------
# Importación de Tienda
# ------------------------------------------------------------------------------
@router.post(
    "/tienda/importar",
    response_model=TiendaImportarResponse,
    summary="Importar datos de tienda (catálogo y ventas)",
)
async def importar_tienda_endpoint(
    archivo: UploadFile = File(..., description="Archivo CSV o JSON de datos de tienda.")
) -> TiendaImportarResponse:
    """Permite actualizar el inventario o cargar datos de una nueva tienda."""
    nombre = (archivo.filename or "").lower()
    if not (nombre.endswith(".csv") or nombre.endswith(".json") or nombre.endswith(".zip")):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Formato de archivo incorrecto",
                "detalle": "Solo se admiten archivos .csv, .json o .zip con la estructura de la tienda.",
            },
        )

    # Validar lectura del archivo
    contenido = await archivo.read()
    if len(contenido) == 0:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Archivo vacío", "detalle": "El archivo enviado no contiene información."},
        )

    # Simulación exitosa de importación (conecta con el importador de Carmen cuando esté listo)
    return TiendaImportarResponse(
        estado="exitoso",
        mensaje=f"Archivo '{archivo.filename}' recibido y validado correctamente.",
        productos_importados=48,
        ventas_importadas=120,
    )
