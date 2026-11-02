import { procesarConsultaNLP } from '../utils/nlpSimulator.js'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Nivel de confianza que se muestra junto a la probabilidad
function nivelConfianza(probabilidad) {
  if (probabilidad >= 0.85) return 'Alta'
  return probabilidad >= 0.6 ? 'Media' : 'Baja'
}

// Convierte la respuesta de POST /chat al formato que usan ChatAssistant y NlpPipelineDrawer.
// Todo sale del modelo real (artifacts/modelo.joblib): intención, probabilidad, top 3 y cada paso
// del preprocesamiento (fases 1-4). Ningún dato se completa con el simulador. (Fernando)
function desdeApi(texto, data) {
  const pasos = data.pasos || {}
  const tokens = pasos.tokens || []
  const probabilidad = data.probabilidad ?? 0
  const noEntendido = data.intencion === 'desconocido' // la confianza no superó el umbral de la API
  const clasificacion = {
    intencion: noEntendido ? 'no_entendido' : data.intencion,
    intencionDetectada: data.intencion_detectada || data.intencion, // la que eligió el modelo
    probabilidad,
    probabilidadPorcentaje: `${(probabilidad * 100).toFixed(1)}%`,
    top3: data.top3 || [],
    modelo: 'Modelo entrenado (modelo.joblib)',
    confianzaNivel: nivelConfianza(probabilidad),
  }
  return {
    fromApi: true,
    intencion: clasificacion.intencion,
    probabilidad,
    entidades: data.entidades || {},
    respuesta: data.respuesta,
    pasos: {
      textoOriginal: pasos.original || texto,
      normalizado: pasos.normalizado || '',
      tokens,
      tokensFormatted: `{ ${tokens.map((t) => `[ ${t} ]`).join(' ')} }`,
      stopWords: {
        eliminadas: pasos.stopwords_eliminadas || [],
        conservadas: pasos.sin_stopwords || [],
      },
      lematizacion: pasos.lemas_o_raices || [],
      entidades: data.entidades || {},
      clasificacion,
    },
  }
}

/**
 * Cliente de comunicación con la API FastAPI.
 * Si la API no responde, usa el simulador del navegador y lo marca como tal (fromApi: false).
 */
export async function enviarMensajeChat(texto, rol = 'cliente') {
  try {
    const controller = new AbortController()
    // 15 s: la primera consulta carga spaCy en el backend y puede tardar varios segundos
    const timeoutId = setTimeout(() => controller.abort(), 15000)

    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ texto, rol }),
      signal: controller.signal
    })

    clearTimeout(timeoutId)

    if (response.ok) {
      return desdeApi(texto, await response.json())
    }
  } catch (err) {
    // Backend no disponible o timeout -> se usa el simulador del navegador
  }

  // Sin API: simulación local, marcada para que la interfaz no la presente como el modelo real
  const localResult = procesarConsultaNLP(texto)
  localResult.clasificacion = {
    ...localResult.clasificacion,
    modelo: 'Simulación local (API apagada)',
  }
  return {
    fromApi: false,
    intencion: localResult.clasificacion.intencion,
    probabilidad: localResult.clasificacion.probabilidad,
    entidades: localResult.entidades,
    respuesta: `${localResult.respuestaConcierge} (Respuesta simulada: la API no está disponible.)`,
    pasos: localResult
  }
}

/**
 * Verificar estado del servicio backend FastAPI
 */
export async function verificarSaludApi() {
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 1200)

    const response = await fetch(`${API_BASE_URL}/health`, {
      signal: controller.signal
    })
    clearTimeout(timeoutId)
    if (response.ok) {
      return await response.json()
    }
  } catch (e) {
    // Offline
  }
  return { estado: 'simulado', modelo_cargado: true, version: '1.0.0 (Local NLP Engine)' }
}

