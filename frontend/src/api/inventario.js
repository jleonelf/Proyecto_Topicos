// Cliente de la API para el apartado "Inventarios y métricas" (Fernando).
// A diferencia del chat, aquí no hay simulación: si la API no responde se
// muestra el error, porque las métricas deben ser siempre las reales.

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Hace la petición y convierte los errores de la API en un mensaje legible
async function pedir(ruta, opciones = {}) {
  let respuesta
  try {
    respuesta = await fetch(`${API_BASE_URL}${ruta}`, opciones)
  } catch {
    throw new Error('No se pudo conectar con la API (¿está levantado el backend en el puerto 8000?).')
  }
  const datos = await respuesta.json().catch(() => ({}))
  if (!respuesta.ok) {
    // La API responde {error, detalle}; FastAPI a veces responde {detail}
    throw new Error(datos.detalle || datos.error || datos.detail || `Error ${respuesta.status}`)
  }
  return datos
}

export const apiInventario = {
  // Métricas del modelo oficial (artifacts/metricas.json)
  metricasEntrenamiento: () => pedir('/metricas/entrenamiento'),

  // Último entrenamiento experimental con un archivo de frases
  ultimoExperimento: () => pedir('/metricas/experimento'),

  // Indicadores y analíticas del inventario y las ventas
  resumenInventario: (umbralStock = 5) => pedir(`/inventario/resumen?umbral_stock=${umbralStock}`),

  // Sube un CSV o Excel; reemplazar=true borra los datos anteriores
  importar: (archivo, reemplazar = false) => {
    const formulario = new FormData()
    formulario.append('archivo', archivo)
    return pedir(`/inventario/importar?reemplazar=${reemplazar}`, { method: 'POST', body: formulario })
  },
}
