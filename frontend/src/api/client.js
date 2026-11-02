import { procesarConsultaNLP } from '../utils/nlpSimulator.js'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/**
 * Cliente de comunicación con la API FastAPI con fallback automático a simulación cliente.
 */
export async function enviarMensajeChat(texto, rol = 'cliente') {
  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 2500)

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
      const data = await response.json()
      // Enriquecer con los pasos estructurados
      const fallback = procesarConsultaNLP(texto)
      return {
        fromApi: true,
        intencion: data.intencion || fallback.clasificacion.intencion,
        probabilidad: data.probabilidad || fallback.clasificacion.probabilidad,
        entidades: data.entidades || fallback.entidades,
        respuesta: data.respuesta || fallback.respuestaConcierge,
        pasos: data.pasos ? {
          original: data.pasos.original || texto,
          normalizado: data.pasos.normalizado,
          tokens: data.pasos.tokens,
          tokensFormatted: `{ ${data.pasos.tokens.map(t => `[ ${t} ]`).join(' ')} }`,
          stopWords: {
            eliminadas: fallback.stopWords.eliminadas,
            conservadas: data.pasos.sin_stopwords || fallback.stopWords.conservadas
          },
          lematizacion: data.pasos.lemas_o_raices || fallback.lematizacion,
          clasificacion: fallback.clasificacion,
          entidades: data.entidades || fallback.entidades
        } : fallback
      }
    }
  } catch (err) {
    // Backend no disponible o timeout -> Usar pipeline local integrado
  }

  // Fallback transparente al pipeline en frontend
  const localResult = procesarConsultaNLP(texto)
  return {
    fromApi: false,
    intencion: localResult.clasificacion.intencion,
    probabilidad: localResult.clasificacion.probabilidad,
    entidades: localResult.entidades,
    respuesta: localResult.respuestaConcierge,
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

