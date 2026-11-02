import React from 'react'

export default function NlpPipelineDrawer({
  isOpen = true,
  currentAnalysis,
  onToggle
}) {
  const analysis = currentAnalysis || {
    textoOriginal: '¿Qué jeans tienen en talla 32 disponibles para envío hoy?',
    normalizado: 'que jeans tienen en talla 32 disponibles para envio hoy',
    tokens: ['que', 'jeans', 'tienen', 'en', 'talla', '32', 'disponibles', 'para', 'envio', 'hoy'],
    stopWords: {
      eliminadas: ['que', 'en', 'para'],
      conservadas: ['jeans', 'tienen', 'talla', '32', 'disponibles', 'envio', 'hoy']
    },
    lematizacion: ['jean', 'tener', 'talla', '32', 'disponible', 'envío', 'hoy'],
    entidades: {
      talla: '32',
      categoria: 'Jeans',
      fecha: 'Hoy'
    },
    clasificacion: {
      intencion: 'consultar_stock',
      probabilidad: 0.992,
      probabilidadPorcentaje: '99.2%',
      modelo: 'Regresión Logística',
      top3: [
        { intencion: 'consultar_stock', probabilidad: 0.992 },
        { intencion: 'consultar_tallas', probabilidad: 0.005 },
        { intencion: 'envios', probabilidad: 0.002 }
      ]
    }
  }

  const tokens = analysis.tokens || ['que', 'jeans', 'tienen', 'en', 'talla', '32', 'disponibles', 'para', 'envio', 'hoy']
  const stopEliminadas = analysis.stopWords?.eliminadas || ['que', 'en', 'para']
  const stopConservadas = analysis.stopWords?.conservadas || ['jeans', 'tienen', 'talla', '32', 'disponibles', 'envio', 'hoy']
  const lemas = analysis.lematizacion || ['jean', 'tener', 'talla', '32', 'disponible', 'envío', 'hoy']
  const top3 = analysis.clasificacion?.top3 || [
    { intencion: 'consultar_stock', probabilidad: 0.992 },
    { intencion: 'consultar_tallas', probabilidad: 0.005 },
    { intencion: 'envios', probabilidad: 0.002 }
  ]

  return (
    <aside className={`nlp-drawer glass-drawer ${isOpen ? 'is-open' : ''}`}>
      {/* Botón de recorrer "<" para alternar / expandir el panel */}
      <button 
        type="button"
        className={`recorrer-toggle-btn ${isOpen ? 'panel-open' : ''}`}
        onClick={onToggle}
        title={isOpen ? 'Ocultar panel de pipeline' : 'Recorrer y ver Cómo se procesa el texto'}
      >
        <span className="recorrer-icon">{isOpen ? '›' : '‹'}</span>
        {!isOpen && <span className="vertical-text">COMO SE PROCESA EL TEXTO</span>}
      </button>

      {/* Contenido del Panel Glassmorphism (Imagen 3) */}
      {isOpen && (
        <div className="drawer-inner">
          {/* Header del Panel */}
          <div className="panel-header">
            <div className="header-left">
              <button type="button" className="back-btn" onClick={onToggle} title="Cerrar panel">
                ‹
              </button>
              <div>
                <span className="panel-tag">RIGHT SECTION</span>
                <h3 className="panel-title">NLP Pipeline Glassmorphism Panel</h3>
              </div>
            </div>
            <span className="model-pill">Regresión Logística</span>
          </div>

          <div className="pipeline-intro">
            <div className="pipeline-main-title">CÓMO SE PROCESA EL TEXTO</div>
            <p className="pipeline-subtitle">
              Los mismos pasos que se usaron al entrenar, ejecutados por el pipeline guardado (Fases 1 a 6).
            </p>
          </div>

          <div className="steps-flow">
            {/* 1. Texto Original */}
            <div className="step-card">
              <div className="step-number-title">
                <span className="step-badge">1</span>
                <h4>Texto Original</h4>
              </div>
              <div className="step-box original-box">
                <p className="step-content original-text">
                  "{analysis.textoOriginal || '¿Qué jeans tienen en talla 32 disponibles para envío hoy?'}"
                </p>
                <div className="step-meta">
                  <span>{(analysis.textoOriginal || '').length} caracteres</span>
                  <span>•</span>
                  <span>{tokens.length} palabras</span>
                </div>
              </div>
            </div>

            {/* 2. Normalización */}
            <div className="step-card">
              <div className="step-number-title">
                <span className="step-badge">2</span>
                <h4>Normalización</h4>
              </div>
              <p className="step-desc">minúsculas, sin puntuación ni acentos diacríticos</p>
              <div className="step-box norm-box">
                <code className="norm-text">
                  {analysis.normalizado || 'que jeans tienen en talla 32 disponibles para envio hoy'}
                </code>
              </div>
            </div>

            {/* 3. Tokenización (Con formato { XX XXXX XXXXXXX } solicitado) */}
            <div className="step-card">
              <div className="step-number-title">
                <span className="step-badge">3</span>
                <h4>Tokenización</h4>
              </div>
              <p className="step-desc">División en tokens individuales de dominio</p>
              <div className="step-box token-box">
                <div className="tokens-bracket-wrapper">
                  <span className="bracket">&#123;</span>
                  <div className="tokens-list">
                    {tokens.map((tok, idx) => (
                      <span key={idx} className="token-chip">
                        [ {tok} ]
                      </span>
                    ))}
                  </div>
                  <span className="bracket">&#125;</span>
                </div>
              </div>
            </div>

            {/* 4. Stop Words */}
            <div className="step-card">
              <div className="step-number-title">
                <span className="step-badge">4</span>
                <h4>Stop Words</h4>
              </div>
              <p className="step-desc">Palabras vacías en español filtradas (se preservan "no", "sin", "más")</p>
              <div className="step-box stopwords-box">
                <div className="stopwords-subgroup">
                  <span className="subgroup-label eliminadas">Eliminadas:</span>
                  <div className="chips-row">
                    {stopEliminadas.map((stop, idx) => (
                      <span key={idx} className="stop-chip removed">
                        <del>{stop}</del>
                      </span>
                    ))}
                    {!stopEliminadas.length && <span className="empty-hint">Ninguna</span>}
                  </div>
                </div>

                <div className="stopwords-subgroup">
                  <span className="subgroup-label conservadas">Se conservan:</span>
                  <div className="chips-row">
                    {stopConservadas.map((tok, idx) => (
                      <span key={idx} className="stop-chip kept">
                        {tok}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* 5. Lematización spaCy */}
            <div className="step-card">
              <div className="step-number-title">
                <span className="step-badge">5</span>
                <h4>Lematización spaCy</h4>
              </div>
              <p className="step-desc">Reducción a lemas raíz con es_core_news_sm</p>
              <div className="step-box lemma-box">
                <div className="chips-row">
                  {lemas.map((lem, idx) => (
                    <span key={idx} className="lemma-chip">
                      {lem}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* 6. Intención & Modelo ML */}
            <div className="step-card">
              <div className="step-number-title">
                <span className="step-badge">6</span>
                <div className="title-with-pill">
                  <h4>Intención &amp; Modelo</h4>
                  <span className="confidence-pill">
                    Confidence {analysis.clasificacion?.probabilidadPorcentaje || '99.2%'}
                  </span>
                </div>
              </div>
              
              <div className="step-box model-box">
                <div className="winner-row">
                  <div className="winner-name">
                    <span className="winner-intent">{analysis.clasificacion?.intencion || 'consultar_stock'}</span>
                    <span className="winner-detail">({analysis.clasificacion?.probabilidadPorcentaje || '99.2%'}) - Regresión Logística</span>
                  </div>
                </div>

                {/* Top 3 Probabilidades con Barras */}
                <div className="top3-container">
                  <span className="top3-title">Distribución Top 3:</span>
                  {top3.map((item) => (
                    <div key={item.intencion} className="top3-row">
                      <div className="top3-label-row">
                        <span className="top3-name">{item.intencion}</span>
                        <span className="top3-pct">{(item.probabilidad * 100).toFixed(1)}%</span>
                      </div>
                      <div className="top3-track">
                        <div className="top3-fill" style={{ width: `${item.probabilidad * 100}%` }}></div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Entidades Extraídas */}
                {analysis.entidades && (
                  <div className="extracted-entities-box">
                    <span className="entities-title">Entidades detectadas (Ramiro - Fase 5):</span>
                    <div className="entities-chips">
                      {analysis.entidades.talla && (
                        <span className="entity-chip">
                          <strong>Talla:</strong> {analysis.entidades.talla}
                        </span>
                      )}
                      {analysis.entidades.categoria && (
                        <span className="entity-chip">
                          <strong>Categoría:</strong> {analysis.entidades.categoria}
                        </span>
                      )}
                      {analysis.entidades.fecha && (
                        <span className="entity-chip">
                          <strong>Envío/Fecha:</strong> {analysis.entidades.fecha}
                        </span>
                      )}
                      {analysis.entidades.color && (
                        <span className="entity-chip">
                          <strong>Color:</strong> {analysis.entidades.color}
                        </span>
                      )}
                    </div>
                  </div>
                )}

                {/* Footer Metadatos de Producción */}
                <div className="pipeline-footer-stats">
                  <span>TF-IDF (1,2) N-Grams (Ramiro - Fase 5)</span>
                  <span>•</span>
                  <span>F1 Macro: 0.8622</span>
                  <span>•</span>
                  <span>Latencia: 8.4 ms</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </aside>
  )
}

