import React from 'react'

export default function Navbar({
  activeTab = 'asistente',
  isApiConnected = false,
  onSelectTab,
  onOpenMetrics,
  onToggleDrawer
}) {
  return (
    <header className="boutique-header">
      {/* Top Safari / Mac Window Mockup Bar (Igual a la Imagen 2) */}
      <div className="mac-window-bar">
        <div className="mac-dots">
          <span className="mac-dot red"></span>
          <span className="mac-dot yellow"></span>
          <span className="mac-dot green"></span>
        </div>
        <div className="mac-url-bar">
          <span className="url-lock">🔒</span> auraboutique.com
        </div>
        <div className="mac-actions">
          <span className={`engine-badge ${isApiConnected ? 'is-api' : ''}`}>
            <span className="pulse-dot"></span>
            {isApiConnected ? 'FastAPI 8000 Online' : 'NLP Engine Activo (React)'}
          </span>
        </div>
      </div>

      {/* Main Navigation Bar */}
      <nav className="main-nav">
        <div className="brand-section">
          <h1 className="brand-title">AURA BOUTIQUE</h1>
          <span className="brand-subtitle">AI Concierge</span>
        </div>

        <div className="nav-links">
          <button 
            type="button"
            className={`nav-item ${activeTab === 'coleccion' ? 'active' : ''}`}
            onClick={() => onSelectTab && onSelectTab('coleccion')}
          >
            [Colección 2026]
          </button>
          <button 
            type="button"
            className={`nav-item ${activeTab === 'metricas' ? 'active' : ''}`}
            onClick={() => onOpenMetrics && onOpenMetrics()}
          >
            [Inventario & Métricas]
          </button>
        </div>

        <div className="user-profile">
          <button 
            type="button"
            className="pipeline-toggle-nav-btn" 
            onClick={() => onToggleDrawer && onToggleDrawer()}
            title="Ver cómo se procesa el texto (Pipeline NLP)"
          >
            <span className="nav-toggle-icon">⚡</span>
            <span>Pipeline NLP</span>
          </button>
          <div className="avatar-ring">
            <img 
              src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&q=80" 
              alt="VIP Member" 
              className="avatar-img"
            />
          </div>
        </div>
      </nav>
    </header>
  )
}

