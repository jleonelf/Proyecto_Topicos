import React, { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react'
import AssistantOrb from './AssistantOrb.jsx'
import { PROMPT_PRESETS } from '../data/mockData.js'

const ChatAssistant = forwardRef(function ChatAssistant({
  latestAnalysis = null,
  isProcessing = false,
  onSendMessage,
  onToggleDrawer
}, ref) {
  const [inputText, setInputText] = useState('')
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const messagesContainerRef = useRef(null)

  // Historial inicial con la conversación exacta de la Imagen 2 & 3
  const [messages, setMessages] = useState([
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

  useImperativeHandle(ref, () => ({
    addAssistantReply: (replyText) => {
      const now = new Date()
      const timeStr = `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`
      setMessages(prev => [
        ...prev,
        {
          sender: 'assistant',
          text: replyText,
          time: timeStr
        }
      ])
    },
    setInput: (txt) => {
      setInputText(txt)
    }
  }))

  useEffect(() => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTop = messagesContainerRef.current.scrollHeight
    }
  }, [messages, isProcessing])

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

  function handleSelectPreset(preset) {
    setInputText(preset.text)
    submitMessage(preset.text)
  }

  function submitMessage(textToSend) {
    const text = (textToSend || inputText).trim()
    if (!text || isProcessing) return

    setInputText('')

    const now = new Date()
    const timeStr = `${now.getHours()}:${String(now.getMinutes()).padStart(2, '0')}`

    setMessages(prev => [
      ...prev,
      {
        sender: 'user',
        text: text,
        time: timeStr
      }
    ])

    onSendMessage && onSendMessage(text)
  }

  function handleSubmit(e) {
    e.preventDefault()
    submitMessage()
  }

  // Web Speech API: Reconocimiento de voz
  const recognitionRef = useRef(null)

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
      if (SpeechRecognition) {
        const sr = new SpeechRecognition()
        sr.lang = 'es-ES'
        sr.continuous = false
        sr.interimResults = false

        sr.onresult = (event) => {
          const transcript = event.results[0][0].transcript
          setInputText(transcript)
          setIsListening(false)
          submitMessage(transcript)
        }
        sr.onerror = () => setIsListening(false)
        sr.onend = () => setIsListening(false)

        recognitionRef.current = sr
      }
    }
  }, [])

  function toggleVoiceListening() {
    if (!recognitionRef.current) {
      alert('Tu navegador no soporta Web Speech API para reconocimiento de voz.')
      return
    }

    if (isListening) {
      recognitionRef.current.stop()
      setIsListening(false)
    } else {
      try {
        recognitionRef.current.start()
        setIsListening(true)
      } catch (err) {
        recognitionRef.current.stop()
        setIsListening(false)
      }
    }
  }

  function speakText(text) {
    if (typeof window === 'undefined' || !window.speechSynthesis) return

    if (isSpeaking) {
      window.speechSynthesis.cancel()
      setIsSpeaking(false)
      return
    }

    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(text)
    utterance.lang = 'es-ES'
    utterance.rate = 1.0
    utterance.pitch = 1.05

    utterance.onstart = () => setIsSpeaking(true)
    utterance.onend = () => setIsSpeaking(false)
    utterance.onerror = () => setIsSpeaking(false)

    window.speechSynthesis.speak(utterance)
  }

  return (
    <div className="chat-assistant-container glass-panel">
      {/* Center Section Header */}
      <div className="assistant-header">
        <div className="center-tag">CENTER SECTION</div>
        <h2 className="assistant-title">Floating luxury VIP Voice &amp; Chat Assistant</h2>
        <p className="assistant-subtitle">Inteligencia Artificial Conversacional con Pipeline NLP Transparente (React 18)</p>
      </div>

      {/* Floating Iridescent Glowing Orb */}
      <AssistantOrb 
        isProcessing={isProcessing}
        isListening={isListening}
        isSpeaking={isSpeaking}
        onClick={toggleVoiceListening}
      />

      {/* Quick Presets Carousel */}
      <div className="presets-bar">
        <span className="preset-label">Probar con:</span>
        <div className="preset-chips">
          {PROMPT_PRESETS.map(preset => (
            <button 
              key={preset.label}
              type="button"
              className="preset-chip"
              onClick={() => handleSelectPreset(preset)}
            >
              {preset.label}
            </button>
          ))}
        </div>
      </div>

      {/* Chat Messages Stream */}
      <div className="messages-stream" ref={messagesContainerRef}>
        {messages.map((msg, index) => (
          <div 
            key={index}
            className={`message-wrapper ${msg.sender}`}
          >
            {msg.sender === 'user' ? (
              <div className="bubble user-bubble">
                <p className="bubble-text">{msg.text}</p>
                <span className="bubble-time">{msg.time}</span>
              </div>
            ) : (
              <div className="assistant-message-row">
                <div className="assistant-avatar">
                  <img 
                    src="https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&w=100&q=80" 
                    alt="Concierge" 
                    className="avatar-photo"
                  />
                </div>
                <div className="bubble assistant-bubble">
                  <div className="assistant-bubble-head">
                    <span className="assistant-name">Concierge</span>
                    <button 
                      type="button"
                      className="speak-btn" 
                      onClick={() => speakText(msg.text)} 
                      title={isSpeaking ? 'Detener voz' : 'Escuchar respuesta en voz alta'}
                    >
                      {isSpeaking ? '🔊' : '🔈'}
                    </button>
                  </div>
                  <p className="bubble-text">{msg.text}</p>
                  <span className="bubble-time">{msg.time}</span>
                </div>
              </div>
            )}
          </div>
        ))}

        {isProcessing && (
          <div className="typing-indicator-row">
            <div className="typing-bubble">
              <span className="dot"></span>
              <span className="dot"></span>
              <span className="dot"></span>
            </div>
          </div>
        )}
      </div>

      {/* NLP Entity & Intent Breakdown Card (Exacto como en la Imagen 2) */}
      {latestAnalysis && (
        <div className="nlp-breakdown-card fade-in">
          <div className="breakdown-header">
            <div className="breakdown-title-row">
              <span className="breakdown-title">NLP Entity &amp; Intent Breakdown</span>
              <span className={`confidence-badge ${latestAnalysis.clasificacion?.confianzaNivel?.toLowerCase() || ''}`}>
                {latestAnalysis.clasificacion?.confianzaNivel || 'Alta'} Confianza
              </span>
            </div>
            <div className="intent-line">
              Intención: <strong>{formatIntentLabel(latestAnalysis.clasificacion?.intencion)}</strong> 
              <span className="intent-pct"> ({latestAnalysis.clasificacion?.probabilidadPorcentaje} Certeza)</span>
            </div>
          </div>

          {/* Animated Progress Bar */}
          <div className="confidence-track">
            <div 
              className="confidence-bar" 
              style={{ width: latestAnalysis.clasificacion?.probabilidadPorcentaje || '99.2%' }}
            ></div>
          </div>

          {/* Badges de Entidades Extraídas */}
          <div className="entities-row">
            {latestAnalysis.entidades?.talla && (
              <span className="entity-badge">
                [Talla: {latestAnalysis.entidades.talla}]
              </span>
            )}
            {latestAnalysis.entidades?.categoria && (
              <span className="entity-badge">
                [Categoría: {latestAnalysis.entidades.categoria}]
              </span>
            )}
            {latestAnalysis.entidades?.fecha && (
              <span className="entity-badge">
                [Envío: {latestAnalysis.entidades.fecha}]
              </span>
            )}
            {latestAnalysis.entidades?.color && (
              <span className="entity-badge">
                [Color: {latestAnalysis.entidades.color}]
              </span>
            )}
          </div>

        </div>
      )}

      {/* Chat Input Form */}
      <form className="chat-input-bar" onSubmit={handleSubmit}>
        <button 
          type="button" 
          className={`mic-btn ${isListening ? 'active' : ''}`}
          onClick={toggleVoiceListening}
          title="Dictar consulta por voz (Web Speech API)"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <line x1="12" x2="12" y1="19" y2="22"></line>
          </svg>
        </button>

        <input 
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          type="text" 
          className="chat-input-field" 
          placeholder="Escribe tu consulta (ej. ¿Tienen jeans en talla 32 disponibles?)..." 
          disabled={isProcessing}
        />

        <button 
          type="submit" 
          className="send-btn" 
          disabled={!inputText.trim() || isProcessing}
        >
          <span>Enviar</span>
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </form>
    </div>
  )
})

export default ChatAssistant

