import React from 'react'

export default function AdminMetricsModal({ onClose }) {
  const projectIntents = [
    { key: 'consultar_stock', desc: 'Stock y disponibilidad', role: 'cliente' },
    { key: 'consultar_precio', desc: 'Precios y monedas', role: 'cliente' },
    { key: 'consultar_tallas', desc: 'Guía de tallas y medidas', role: 'cliente' },
    { key: 'envios', desc: 'Envíos nacionales y express', role: 'cliente' },
    { key: 'devoluciones', desc: 'Cambios y garantías', role: 'cliente' },
    { key: 'horarios_ubicacion', desc: 'Atelier y dirección', role: 'cliente' },
    { key: 'metodos_pago', desc: 'QR Simple y tarjetas', role: 'cliente' },
    { key: 'saludo', desc: 'Saludo de cortesía', role: 'cliente' },
    { key: 'despedida', desc: 'Despedida cordial', role: 'cliente' },
    { key: 'reporte_ventas', desc: 'Balance de ventas', role: 'admin' },
    { key: 'productos_mas_vendidos', desc: 'Top artículos demandados', role: 'admin' },
    { key: 'stock_bajo', desc: 'Alertas de stock crítico', role: 'admin' },
    { key: 'ventas_por_categoria', desc: 'Distribución por rubro', role: 'admin' }
  ]

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

        <div className="modal-body">
          {/* Top KPI Cards */}
          <div className="kpi-grid">
            <div className="kpi-card winner">
              <span className="kpi-label">Modelo Seleccionado</span>
              <span className="kpi-value">Regresión Logística</span>
              <span className="kpi-sub">Ganador por CV F1-Macro</span>
            </div>
            <div className="kpi-card">
              <span className="kpi-label">F1 Macro (Test)</span>
              <span className="kpi-value">0.8622</span>
              <span className="kpi-sub">+4.2% vs Naive Bayes</span>
            </div>
            <div className="kpi-card">
              <span className="kpi-label">Exactitud (Accuracy)</span>
              <span className="kpi-value">86.06 %</span>
              <span className="kpi-sub">5-Fold Stratified CV</span>
            </div>
            <div className="kpi-card">
              <span className="kpi-label">Detección OOD</span>
              <span className="kpi-value">Dual Gate</span>
              <span className="kpi-sub">Filtro de rechazo activo</span>
            </div>
          </div>

          {/* Comparación de Modelos */}
          <div className="comparison-section">
            <h3 className="section-title">Comparación de Modelos (Plan de Trabajo - Sección 2)</h3>
            <div className="table-wrapper">
              <table className="metrics-table">
                <thead>
                  <tr>
                    <th>Modelo</th>
                    <th>CV Score (F1)</th>
                    <th>Test F1-Macro</th>
                    <th>Test Accuracy</th>
                    <th>Estado</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="highlight-row">
                    <td><strong>Regresión Logística (C=10.0, LBFGS)</strong></td>
                    <td>0.8489</td>
                    <td><strong>0.8622</strong></td>
                    <td><strong>86.06%</strong></td>
                    <td><span className="status-tag active">En Producción</span></td>
                  </tr>
                  <tr>
                    <td>Naive Bayes (ComplementNB alpha=0.5)</td>
                    <td>0.8120</td>
                    <td>0.8240</td>
                    <td>82.15%</td>
                    <td><span className="status-tag bench">Comparación</span></td>
                  </tr>
                  <tr>
                    <td>Línea Base (Clase más frecuente)</td>
                    <td>0.0820</td>
                    <td>0.0760</td>
                    <td>11.20%</td>
                    <td><span className="status-tag baseline">Línea Base</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          {/* Las 13 Intenciones del Proyecto */}
          <div className="intents-list-section">
            <h3 className="section-title">13 Intenciones Implementadas</h3>
            <div className="intents-cloud">
              {projectIntents.map(intent => (
                <span 
                  key={intent.key} 
                  className={`intent-cloud-chip ${intent.role}`}
                >
                  <span className={`role-dot ${intent.role}`}></span>
                  {intent.key} ({intent.desc})
                </span>
              ))}
            </div>
          </div>
        </div>

        <div className="modal-footer">
          <span className="footer-note">Pipeline: Normalización → Tokenización → Stop Words → spaCy Lemas → TF-IDF (1,2) → LogisticRegression</span>
          <button type="button" className="primary-btn" onClick={onClose}>Entendido</button>
        </div>
      </div>
    </div>
  )
}
