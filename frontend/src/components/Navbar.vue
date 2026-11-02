<template>
  <header class="boutique-header">
    <!-- Top Safari / Mac Window Mockup Bar (Igual a la Imagen 2) -->
    <div class="mac-window-bar">
      <div class="mac-dots">
        <span class="mac-dot red"></span>
        <span class="mac-dot yellow"></span>
        <span class="mac-dot green"></span>
      </div>
      <div class="mac-url-bar">
        <span class="url-lock">🔒</span> auraboutique.com
      </div>
      <div class="mac-actions">
        <span class="engine-badge" :class="{ 'is-api': isApiConnected }">
          <span class="pulse-dot"></span>
          {{ isApiConnected ? 'FastAPI 8000 Online' : 'NLP Engine Activo' }}
        </span>
      </div>
    </div>

    <!-- Main Navigation Bar -->
    <nav class="main-nav">
      <div class="brand-section">
        <h1 class="brand-title">AURA BOUTIQUE</h1>
        <span class="brand-subtitle">AI Concierge</span>
      </div>

      <div class="nav-links">
        <button 
          class="nav-item" 
          :class="{ active: activeTab === 'coleccion' }"
          @click="$emit('select-tab', 'coleccion')"
        >
          [Colección 2026]
        </button>
        <button 
          class="nav-item" 
          :class="{ active: activeTab === 'metricas' }"
          @click="$emit('open-metrics')"
        >
          [Inventario & Métricas]
        </button>
      </div>

      <div class="user-profile">
        <button 
          class="pipeline-toggle-nav-btn" 
          @click="$emit('toggle-drawer')"
          title="Ver cómo se procesa el texto (Pipeline NLP)"
        >
          <span class="nav-toggle-icon">⚡</span>
          <span>Pipeline NLP</span>
        </button>
        <div class="avatar-ring">
          <img 
            src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&w=120&q=80" 
            alt="VIP Member" 
            class="avatar-img"
          />
        </div>
      </div>
    </nav>
  </header>
</template>

<script setup>
defineProps({
  activeTab: {
    type: String,
    default: 'asistente'
  },
  isApiConnected: {
    type: Boolean,
    default: false
  }
})

defineEmits(['select-tab', 'open-metrics', 'toggle-drawer'])
</script>

<style scoped>
.boutique-header {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(210, 195, 175, 0.45);
  position: sticky;
  top: 0;
  z-index: 50;
  transition: all 0.3s ease;
}

.mac-window-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 20px;
  background: rgba(247, 244, 238, 0.9);
  border-bottom: 1px solid rgba(210, 195, 175, 0.3);
  font-size: 0.76rem;
}

.mac-dots {
  display: flex;
  gap: 7px;
}
.mac-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}
.mac-dot.red { background: #ff5f56; }
.mac-dot.yellow { background: #ffbd2e; }
.mac-dot.green { background: #27c93f; }

.mac-url-bar {
  background: rgba(255, 255, 255, 0.9);
  padding: 4px 18px;
  border-radius: 999px;
  font-family: var(--font-mono);
  font-size: 0.74rem;
  color: #555;
  border: 1px solid rgba(210, 195, 175, 0.4);
  letter-spacing: 0.02em;
}
.url-lock {
  font-size: 0.68rem;
  margin-right: 4px;
}

.engine-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.72rem;
  font-weight: 500;
  color: #7b6953;
  background: #f4ecdf;
  padding: 3px 10px;
  border-radius: 999px;
  border: 1px solid rgba(197, 168, 128, 0.3);
}
.engine-badge.is-api {
  color: #1b5e20;
  background: #e8f5e9;
  border-color: #a5d6a7;
}
.pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #b3884d;
  display: inline-block;
  animation: pulse 1.6s infinite;
}
.engine-badge.is-api .pulse-dot {
  background: #2e7d32;
}

@keyframes pulse {
  0% { transform: scale(0.9); opacity: 0.6; }
  50% { transform: scale(1.3); opacity: 1; }
  100% { transform: scale(0.9); opacity: 0.6; }
}

.main-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 28px;
  max-width: 1560px;
  margin: 0 auto;
}

.brand-section {
  display: flex;
  flex-direction: column;
}

.brand-title {
  font-family: var(--font-serif);
  font-size: 1.65rem;
  letter-spacing: 0.18em;
  font-weight: 600;
  color: #1a1816;
  line-height: 1;
}

.brand-subtitle {
  font-size: 0.72rem;
  letter-spacing: 0.22em;
  text-transform: uppercase;
  color: #9c8466;
  font-weight: 500;
  margin-top: 3px;
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 12px;
}

.nav-item {
  background: transparent;
  border: none;
  font-family: var(--font-sans);
  font-size: 0.88rem;
  color: #635b51;
  cursor: pointer;
  padding: 6px 14px;
  border-radius: 8px;
  transition: all 0.2s ease;
  font-weight: 500;
}

.nav-item:hover {
  color: #1a1816;
  background: rgba(197, 168, 128, 0.12);
}

.nav-item.active {
  color: #1a1816;
  border-bottom: 2px solid #b3884d;
  font-weight: 600;
}

.nav-item.highlight {
  color: #1a1816;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 14px;
}

.pipeline-toggle-nav-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: #27223b;
  color: #ffffff;
  border: none;
  padding: 7px 14px;
  border-radius: 999px;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(39, 34, 59, 0.2);
  transition: all 0.2s ease;
}

.pipeline-toggle-nav-btn:hover {
  background: #3c3459;
  transform: translateY(-1px);
}

.avatar-ring {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  padding: 2px;
  background: linear-gradient(135deg, #c5a880, #e8dbc6);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.avatar-img {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}
</style>

