import React from 'react'

export default function AssistantOrb({
  isProcessing = false,
  isListening = false,
  isSpeaking = false,
  onClick
}) {
  return (
    <div className="orb-container" onClick={onClick}>
      <div 
        className={`iridescent-orb ${isProcessing ? 'is-processing' : ''} ${isListening ? 'is-listening' : ''} ${isSpeaking ? 'is-speaking' : ''}`}
      >
        <div className="orb-specular"></div>
        <div className="orb-inner-wave"></div>
      </div>
      <div className="orb-reflection"></div>
      <div className="orb-status-caption">
        {isListening ? (
          <span className="status-chip listening">
            <span className="mic-dot"></span> Escuchando voz...
          </span>
        ) : isSpeaking ? (
          <span className="status-chip speaking">
            <span className="audio-waves"></span> Concierge hablando...
          </span>
        ) : isProcessing ? (
          <span className="status-chip processing">
            <span className="spin-dot"></span> Procesando NLP...
          </span>
        ) : (
          <span className="status-chip idle">
            ✨ Aura AI Concierge VIP
          </span>
        )}
      </div>
    </div>
  )
}

