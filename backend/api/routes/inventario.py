"""Endpoints del apartado "Inventarios y métricas".

Responsable: Fernando.

    GET  /metricas/entrenamiento   métricas del modelo oficial (artifacts/metricas.json)
    GET  /metricas/experimento     último entrenamiento experimental
    GET  /inventario/resumen       indicadores y analíticas del inventario y las ventas
    POST /inventario/importar      importación masiva de CSV o Excel
"""

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from api.services.metricas_service import metricas_entrenamiento
from src.data.inventario import ArchivoInvalido, importar_tablas, leer_archivo, resumen_inventario
from src.models.experimento import DatosInsuficientes, entrenar_experimento, ultimo_experimento

router = APIRouter(tags=["Inventarios y métricas"])


@router.get("/metricas/entrenamiento", summary="Métricas del entrenamiento oficial")
def get_metricas_entrenamiento():
    """Comparación de modelos, métricas por intención, matriz de confusión y términos influyentes."""
    return metricas_entrenamiento()


@router.get("/metricas/experimento", summary="Último entrenamiento experimental")
def get_metricas_experimento():
    """Métricas del último modelo entrenado con un archivo de frases subido por el usuario."""
    return ultimo_experimento()


@router.get("/inventario/resumen", summary="Analíticas del inventario y las ventas")
def get_resumen_inventario(
    umbral_stock: int = Query(5, ge=0, le=1000, description="Stock máximo para considerar un producto en alerta"),
):
    """Indicadores, más vendidos, ventas por categoría y por fecha, y productos con stock bajo."""
    return resumen_inventario(umbral_stock=umbral_stock)


@router.post("/inventario/importar", summary="Importación masiva de inventario (CSV o Excel)")
async def post_importar_inventario(
    archivo: UploadFile = File(..., description="Archivo .csv, .xlsx o .xls con productos, ventas o frases."),
    reemplazar: bool = Query(False, description="Borrar los datos anteriores antes de importar"),
):
    """Importa productos y ventas a la base de datos.

    Si el archivo trae frases etiquetadas (texto, intencion), además entrena un
    modelo experimental y devuelve sus métricas comparadas con el modelo oficial.
    """
    contenido = await archivo.read()
    try:
        hojas = leer_archivo(archivo.filename, contenido)
        # La importación y el entrenamiento son trabajo pesado: se ejecutan en un
        # hilo aparte para no bloquear las demás peticiones de la API
        resultado = await run_in_threadpool(importar_tablas, hojas, reemplazar)
        experimento = None
        if resultado["frases"]:
            experimento = await run_in_threadpool(entrenar_experimento, resultado["frases"], archivo.filename)
    except ArchivoInvalido as exc:
        return JSONResponse(status_code=400, content={"error": "Archivo inválido", "detalle": str(exc)})
    except DatosInsuficientes as exc:
        return JSONResponse(status_code=422, content={"error": "Datos insuficientes", "detalle": str(exc)})
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"No se pudo importar el archivo: {exc}") from None

    return {
        "archivo": archivo.filename,
        "hojas": resultado["hojas"],
        "experimento": experimento,
        "inventario": resumen_inventario(),  # analíticas actualizadas tras la importación
    }
