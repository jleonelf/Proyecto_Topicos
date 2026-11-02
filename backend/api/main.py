"""Punto de entrada principal para la API REST con FastAPI.

Responsable: Ramiro (Backend)
Funcionalidades:
    - Inicialización de la aplicación FastAPI y documentación interactiva OpenAPI (/docs).
    - Middleware de CORS configurado desde src/config.yaml.
    - Manejador personalizado para errores de validación (HTTP 422) con mensajes en español.
    - Endpoint de diagnóstico GET /health que monitorea el estado del servicio y los artefactos.
"""

from pathlib import Path
from typing import Any, Dict
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config import config
from api.schemas import HealthResponse, ErrorDetalleResponse
from api.routes.chat import router as chat_router
from api.routes.reportes import router as reportes_router

# Directorio raíz del proyecto
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

# Configuración de metadatos de la aplicación
app = FastAPI(
    title=config.get("proyecto", {}).get("nombre", "Asistente Tiendas de Ropa"),
    description=(
        "API REST para clasificación de intenciones de clientes y administradores "
        "de tiendas de ropa mediante procesamiento de lenguaje natural y machine learning."
    ),
    version=config.get("proyecto", {}).get("version", "1.0.0"),
    docs_url="/docs",
    redoc_url="/redoc",
)

# ------------------------------------------------------------------------------
# Configuración de CORS (Cross-Origin Resource Sharing)
# ------------------------------------------------------------------------------
origenes_cors = config.get("api", {}).get("cors", {}).get(
    "permitir_origenes",
    ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_cors,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# Inclusión de Routers
# ------------------------------------------------------------------------------
app.include_router(chat_router)
app.include_router(reportes_router)


# ------------------------------------------------------------------------------
# Manejador de errores de validación de entradas (HTTP 422)
# ------------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def manejador_errores_validacion(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Transforma errores de validación de Pydantic en respuestas legibles en español."""
    mensajes = []
    for err in exc.errors():
        msg = err.get("msg", "Dato de entrada no válido.")
        # Limpiar prefijo común de Pydantic si está presente
        if "Value error," in msg:
            msg = msg.replace("Value error,", "").strip()
        mensajes.append(msg)

    detalle = " | ".join(mensajes) if mensajes else "Parámetros de entrada inválidos."
    return JSONResponse(
        status_code=422,
        content={"error": "Error de validación", "detalle": detalle},
    )


# ------------------------------------------------------------------------------
# Endpoints base
# ------------------------------------------------------------------------------
@app.get(
    "/",
    summary="Ruta raíz de bienvenida",
    tags=["General"],
)
async def root() -> Dict[str, Any]:
    """Retorna información general de la API y enlaces a la documentación."""
    return {
        "mensaje": "Bienvenido a la API del Asistente para Tiendas de Ropa",
        "documentacion": "/docs",
        "salud": "/health",
        "version": app.version,
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Estado de salud y diagnóstico del servicio",
    tags=["Diagnóstico"],
)
async def health() -> HealthResponse:
    """Verifica si la API está activa y si los artefactos requeridos están disponibles.

    No falla si el modelo o la base de datos aún no existen; informa su estado
    de forma transparente para permitir despliegues y pruebas modulares.
    """
    ruta_modelo_rel = config.get("rutas", {}).get(
        "modelo_guardado", "artifacts/modelo.joblib"
    )
    ruta_tienda_rel = config.get("rutas", {}).get(
        "base_datos_tienda", "artifacts/tienda.db"
    )

    ruta_modelo = RAIZ_PROYECTO / ruta_modelo_rel
    ruta_tienda = RAIZ_PROYECTO / ruta_tienda_rel

    modelo_existe = ruta_modelo.is_file()
    tienda_existe = ruta_tienda.is_file()

    return HealthResponse(
        estado="activo",
        version=app.version,
        modelo_cargado=modelo_existe,
        tienda_cargada=tienda_existe,
        detalles={
            "ruta_modelo": str(ruta_modelo_rel),
            "modelo_disponible": modelo_existe,
            "ruta_tienda": str(ruta_tienda_rel),
            "tienda_disponible": tienda_existe,
        },
    )
