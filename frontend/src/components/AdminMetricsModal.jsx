import React from 'react'

export default function AdminMetricsModal({ onClose }) {

  return (
    <div className="modal-backdrop" onClick={(e) => {
      if (e.target === e.currentTarget) onClose && onClose()
    }}>
      <div className="modal-card glass-panel fade-in">
        <div className="modal-header">
          <div>
            <span className="modal-tag">EVALUACIÓN &amp; ML METRICS</span>
            <h2 className="modal-title">Métricas de Producción del Modelo</h2>
            <p className="modal-subtitle">Resultados oficiales generados en artifacts/metricas.json (Jorge - Fase 6)</p>
          </div>
          <button type="button" className="close-btn" onClick={onClose}>✕</button>
        </div>
      </div>
    </div>
  )
}

