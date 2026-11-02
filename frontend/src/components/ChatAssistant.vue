<template>
  <div class="chat-assistant-container glass-panel">
    <!-- Center Section Header -->
    <div class="assistant-header">
      <div class="center-tag">CENTER SECTION</div>
      <h2 class="assistant-title">Floating luxury VIP Voice & Chat Assistant</h2>
      <p class="assistant-subtitle">Inteligencia Artificial Conversacional con Pipeline NLP Transparente</p>
    </div>

    <!-- Floating Iridescent Glowing Orb -->
    <AssistantOrb 
      :is-processing="isProcessing"
      :is-listening="isListening"
      :is-speaking="isSpeaking"
      @click="toggleVoiceListening"
    />

    <!-- Quick Presets Carousel (Similar a la Imagen 1 del profesor, adaptado a Tienda de Ropa) -->
    <div class="presets-bar">
      <span class="preset-label">Probar con:</span>
      <div class="preset-chips">
        <button 
          v-for="preset in presets" 
          :key="preset.label"
          class="preset-chip"
          @click="selectPreset(preset)"
        >
          {{ preset.label }}
        </button>
      </div>
    </div>

    <!-- Chat Messages Stream -->
    <div class="messages-stream" ref="messagesContainer">
      <div 
        v-for="(msg, index) in messages" 
        :key="index"
        class="message-wrapper"
        :class="msg.sender"
      >
        <!-- User Bubble (Dark Indigo Luxury, matching Image 2) -->
        <div v-if="msg.sender === 'user'" class="bubble user-bubble">
          <p class="bubble-text">{{ msg.text }}</p>
          <span class="bubble-time">{{ msg.time }}</span>
        </div>

        <!-- Assistant Bubble (Soft Cream / Luxury Card with Avatar) -->
        <div v-else class="assistant-message-row">
          <div class="assistant-avatar">
            <img 
              src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=100&q=80" 
              alt="Concierge" 
              class="avatar-photo"
            />
          </div>
          <div class="bubble assistant-bubble">
            <div class="assistant-bubble-head">
              <span class="assistant-name">Concierge</span>
              <button 
                class="speak-btn" 
                @click="speakText(msg.text)" 
                :title="isSpeaking ? 'Detener voz' : 'Escuchar respuesta en voz alta'"
              >
                {{ isSpeaking ? '🔊' : '🔈' }}
              </button>
            </div>
            <p class="bubble-text">{{ msg.text }}</p>
            <span class="bubble-time">{{ msg.time }}</span>
          </div>
        </div>
      </div>

      <!-- Typing Indicator -->
      <div v-if="isProcessing" class="typing-indicator-row">
        <div class="typing-bubble">
          <span class="dot"></span>
          <span class="dot"></span>
          <span class="dot"></span>
        </div>
      </div>
    </div>

    <!-- NLP Entity & Intent Breakdown Card (Exacto como en la Imagen 2) -->
    <div v-if="latestAnalysis" class="nlp-breakdown-card fade-in">
      <div class="breakdown-header">
        <div class="breakdown-title-row">
          <span class="breakdown-title">NLP Entity & Intent Breakdown</span>
          <span class="confidence-badge" :class="latestAnalysis.clasificacion.confianzaNivel.toLowerCase()">
            {{ latestAnalysis.clasificacion.confianzaNivel }} Confianza
          </span>
        </div>
        <div class="intent-line">
          Intención: <strong>{{ formatIntentLabel(latestAnalysis.clasificacion.intencion) }}</strong> 
          <span class="intent-pct">({{ latestAnalysis.clasificacion.probabilidadPorcentaje }} Certeza)</span>
        </div>
      </div>

      <!-- Animated Progress Bar (Gradiente azul-púrpura como en la Imagen 2) -->
      <div class="confidence-track">
        <div 
          class="confidence-bar" 
          :style="{ width: latestAnalysis.clasificacion.probabilidadPorcentaje }"
        ></div>
      </div>

      <!-- Badges de Entidades Extraídas [Talla: 32] [Categoría: Jeans] [Envío: Hoy] -->
      <div class="entities-row">
        <span v-if="latestAnalysis.entidades.talla" class="entity-badge">
          [Talla: {{ latestAnalysis.entidades.talla }}]
        </span>
        <span v-if="latestAnalysis.entidades.categoria" class="entity-badge">
          [Categoría: {{ latestAnalysis.entidades.categoria }}]
        </span>
        <span v-if="latestAnalysis.entidades.fecha" class="entity-badge">
          [Envío: {{ latestAnalysis.entidades.fecha }}]
        </span>
        <span v-if="latestAnalysis.entidades.color" class="entity-badge">
          [Color: {{ latestAnalysis.entidades.color }}]
        </span>
      </div>

    </div>

    <!-- Chat Input Form -->
    <form class="chat-input-bar" @submit.prevent="handleSubmit">
      <button 
        type="button" 
        class="mic-btn" 
        :class="{ active: isListening }"
        @click="toggleVoiceListening"
        title="Dictar consulta por voz (Web Speech API)"
      >
        <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
          <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
          <line x1="12" x2="12" y1="19" y2="22"></line>
        </svg>
      </button>

      <input 
        v-model="inputText" 
        type="text" 
        class="chat-input-field" 
        placeholder="Escribe tu consulta (ej. ¿Tienen jeans en talla 32 disponibles?)..." 
        :disabled="isProcessing"
      />

      <button 
        type="submit" 
        class="send-btn" 
        :disabled="!inputText.trim() || isProcessing"
      >
        <span>Enviar</span>
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"></line>
          <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
        </svg>
      </button>
    </form>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import AssistantOrb from './AssistantOrb.vue'
import { PROMPT_PRESETS } from '../data/mockData.js'

const props = defineProps({
  latestAnalysis: {
    type: Object,
    default: null
  },
  isProcessing: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['send-message', 'toggle-drawer'])

const presets = PROMPT_PRESETS
const inputText = ref('')
const messagesContainer = ref(null)
const isListening = ref(false)
const isSpeaking = ref(false)

// Historial inicial con la conversación exacta de la Imagen 2 & 3
const messages = ref([
  {
    sender: 'user',
    text: '¿Qué jeans tienen en talla 32 disponibles para envío hoy?',
    time: '16:29'
  },
  {
    sender: 'assistant',
    text: 'Tenemos el Denim Slim Raw en talla 32 listo para despacho inmediato con QR.',
    time: '16:29'
  }
])

function formatIntentLabel(intent) {
  const map = {
    consultar_stock: 'Consulta Inventario',
    consultar_precio: 'Consulta de Precios',
    consultar_tallas: 'Disponibilidad de Tallas',
    envios: 'Políticas y Envíos',
    devoluciones: 'Cambios y Devoluciones',
    horarios_ubicacion: 'Horarios & Atelier',
    metodos_pago: 'Formas de Pago QR/Tarjeta',
    reporte_ventas: 'Reporte de Ventas (Admin)',
    productos_mas_vendidos: 'Más Vendidos (Admin)',
    stock_bajo: 'Alerta Stock Bajo (Admin)',
    ventas_por_categoria: 'Ventas por Categoría',
    saludo: 'Saludo Protocolar',
    despedida: 'Despedida'
  }
  return map[intent] || intent
}

function selectPreset(preset) {
  inputText.value = preset.text
  handleSubmit()
}

function handleSubmit() {
  if (!inputText.value.trim() || props.isProcessing) return
  const text = inputText.value.trim()
  inputText.value = ''

  const now = new Date()
  const timeStr = `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`

  // Agregar mensaje de usuario
  messages.value.push({
    sender: 'user',
    text: text,
    time: timeStr
  })

  scrollToBottom()
  emit('send-message', text)
}

function addAssistantReply(replyText) {
  const now = new Date()
  const timeStr = `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`

  messages.value.push({
    sender: 'assistant',
    text: replyText,
    time: timeStr
  })
  scrollToBottom()
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesContainer.value) {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    }
  })
}

// Integración de Web Speech API (Voz según PLAN_DE_TRABAJO.md)
let speechRecognition = null

onMounted(() => {
  if (typeof window !== 'undefined') {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (SpeechRecognition) {
      speechRecognition = new SpeechRecognition()
      speechRecognition.lang = 'es-ES'
      speechRecognition.continuous = false
      speechRecognition.interimResults = false

      speechRecognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript
        inputText.value = transcript
        isListening.value = false
        handleSubmit()
      }

      speechRecognition.onerror = () => {
        isListening.value = false
      }

      speechRecognition.onend = () => {
        isListening.value = false
      }
    }
  }
})

function toggleVoiceListening() {
  if (!speechRecognition) {
    alert('Tu navegador no soporta Web Speech API para reconocimiento de voz.')
    return
  }

  if (isListening.value) {
    speechRecognition.stop()
    isListening.value = false
  } else {
    try {
      speechRecognition.start()
      isListening.value = true
    } catch (e) {
      speechRecognition.stop()
      isListening.value = false
    }
  }
}

function speakText(text) {
  if (typeof window === 'undefined' || !window.speechSynthesis) return

  if (isSpeaking.value) {
    window.speechSynthesis.cancel()
    isSpeaking.value = false
    return
  }

  window.speechSynthesis.cancel()
  const utterance = new SpeechSynthesisUtterance(text)
  utterance.lang = 'es-ES'
  utterance.rate = 1.0
  utterance.pitch = 1.05

  utterance.onstart = () => { isSpeaking.value = true }
  utterance.onend = () => { isSpeaking.value = false }
  utterance.onerror = () => { isSpeaking.value = false }

  window.speechSynthesis.speak(utterance)
}

defineExpose({
  addAssistantReply,
  setInput: (txt) => { inputText.value = txt }
})
</script>

<style scoped>
.chat-assistant-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 650px;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(20px);
  border-radius: 24px;
  border: 1px solid rgba(210, 195, 175, 0.5);
  box-shadow: 0 16px 45px rgba(39, 34, 59, 0.08);
  padding: 22px;
  position: relative;
  overflow: hidden;
}

.assistant-header {
  text-align: center;
  margin-bottom: 4px;
}

.center-tag {
  font-size: 0.68rem;
  letter-spacing: 0.2em;
  color: #9c8466;
  text-transform: uppercase;
  font-weight: 600;
}

.assistant-title {
  font-family: var(--font-serif);
  font-size: 1.45rem;
  font-weight: 600;
  color: #1a1816;
  line-height: 1.2;
  margin-top: 2px;
}

.assistant-subtitle {
  font-size: 0.74rem;
  color: #827b73;
}

/* Presets Bar */
.presets-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 10px 0 14px;
  overflow-x: auto;
  padding-bottom: 4px;
}

.preset-label {
  font-size: 0.72rem;
  color: #827b73;
  white-space: nowrap;
  font-weight: 600;
}

.preset-chips {
  display: flex;
  gap: 6px;
  flex-wrap: nowrap;
}

.preset-chip {
  background: rgba(247, 244, 238, 0.95);
  border: 1px solid rgba(210, 195, 175, 0.45);
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 0.72rem;
  color: #554e46;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s ease;
  font-weight: 500;
}

.preset-chip:hover {
  background: #27223b;
  color: white;
  border-color: #27223b;
}

/* Messages Stream */
.messages-stream {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 8px 4px;
  max-height: 280px;
  min-height: 180px;
}

.message-wrapper {
  display: flex;
  width: 100%;
}

.message-wrapper.user {
  justify-content: flex-end;
}

.user-bubble {
  background: #27223b; /* Deep Indigo matching Image 2 */
  color: #ffffff;
  padding: 12px 18px;
  border-radius: 18px 18px 4px 18px;
  max-width: 82%;
  box-shadow: 0 4px 14px rgba(39, 34, 59, 0.15);
}

.assistant-message-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  max-width: 90%;
}

.assistant-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  border: 1px solid rgba(197, 168, 128, 0.5);
  margin-top: 4px;
}

.avatar-photo {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.assistant-bubble {
  background: #fdfbf7;
  border: 1px solid rgba(210, 195, 175, 0.4);
  color: #2d2a26;
  padding: 12px 16px;
  border-radius: 4px 18px 18px 18px;
  box-shadow: 0 4px 16px rgba(39, 34, 59, 0.05);
  flex: 1;
}

.assistant-bubble-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.assistant-name {
  font-size: 0.72rem;
  font-weight: 700;
  color: #9c8466;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.speak-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 0.85rem;
  opacity: 0.6;
  transition: opacity 0.2s;
}
.speak-btn:hover {
  opacity: 1;
}

.bubble-text {
  font-size: 0.88rem;
  line-height: 1.45;
}

.bubble-time {
  display: block;
  font-size: 0.65rem;
  margin-top: 4px;
  opacity: 0.6;
  text-align: right;
}

/* Typing Indicator */
.typing-indicator-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 0;
}
.typing-bubble {
  background: #f4ecdf;
  padding: 8px 14px;
  border-radius: 999px;
  display: flex;
  gap: 4px;
}
.typing-bubble .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #9c8466;
  animation: bounce 1.2s infinite;
}
.typing-bubble .dot:nth-child(2) { animation-delay: 0.2s; }
.typing-bubble .dot:nth-child(3) { animation-delay: 0.4s; }

@keyframes bounce {
  0%, 80%, 100% { transform: translateY(0); }
  40% { transform: translateY(-4px); }
}

/* NLP Breakdown Card (Image 2) */
.nlp-breakdown-card {
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(210, 195, 175, 0.4);
  border-radius: 16px;
  padding: 14px 16px;
  margin-top: 10px;
  box-shadow: 0 6px 20px rgba(39, 34, 59, 0.06);
}

.breakdown-header {
  margin-bottom: 8px;
}

.breakdown-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.breakdown-title {
  font-size: 0.78rem;
  font-weight: 700;
  color: #1a1816;
  letter-spacing: 0.02em;
}

.confidence-badge {
  font-size: 0.68rem;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 999px;
  background: #e8f5e9;
  color: #2e7d32;
}

.confidence-badge.media {
  background: #fff8e1;
  color: #f57f17;
}

.intent-line {
  font-size: 0.8rem;
  color: #4a453f;
  margin-top: 3px;
}

.intent-pct {
  color: #5c3c92;
  font-weight: 600;
}

.confidence-track {
  width: 100%;
  height: 6px;
  background: #eee8de;
  border-radius: 999px;
  overflow: hidden;
  margin: 6px 0 10px;
}

.confidence-bar {
  height: 100%;
  background: linear-gradient(90deg, #5c3c92, #3b82f6);
  border-radius: 999px;
  transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

.entities-row {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.entity-badge {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  background: #f4ecdf;
  color: #5c4a32;
  padding: 3px 9px;
  border-radius: 6px;
  border: 1px solid rgba(197, 168, 128, 0.35);
}

/* Call to Action: Open Pipeline Button */
.open-pipeline-btn {
  width: 100%;
  background: #1f1b2e; /* Dark sleek pill button */
  color: #ffffff;
  border: none;
  border-radius: 12px;
  padding: 10px 14px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  box-shadow: 0 4px 14px rgba(31, 27, 46, 0.25);
  transition: all 0.25s ease;
}

.open-pipeline-btn:hover {
  background: #312a47;
  transform: translateY(-2px);
  box-shadow: 0 6px 18px rgba(31, 27, 46, 0.35);
}

.pipeline-btn-icon {
  font-size: 0.85rem;
}

.pipeline-btn-text {
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.pipeline-btn-sub {
  font-size: 0.65rem;
  color: #cbbad8;
  letter-spacing: 0.04em;
}

/* Chat Input Bar */
.chat-input-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(210, 195, 175, 0.5);
  border-radius: 999px;
  padding: 6px 8px 6px 14px;
  box-shadow: 0 4px 14px rgba(39, 34, 59, 0.04);
}

.mic-btn {
  background: transparent;
  border: none;
  color: #7b746a;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px;
  border-radius: 50%;
  transition: all 0.2s;
}

.mic-btn:hover {
  color: #1a1816;
  background: #f4ecdf;
}

.mic-btn.active {
  color: #c53030;
  background: #fde8e8;
  animation: pulse 1.2s infinite;
}

.chat-input-field {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 0.86rem;
  font-family: var(--font-sans);
  color: #1a1816;
}

.chat-input-field::placeholder {
  color: #a39c92;
}

.send-btn {
  background: #27223b;
  color: #ffffff;
  border: none;
  border-radius: 999px;
  padding: 8px 16px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
}

.send-btn:hover:not(:disabled) {
  background: #b3884d;
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>

