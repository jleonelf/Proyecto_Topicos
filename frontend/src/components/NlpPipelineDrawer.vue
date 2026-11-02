<template>
  <aside 
    class="nlp-drawer glass-drawer" 
    :class="{ 'is-open': isOpen }"
  >
    <!-- Botón de recorrer "<" para alternar / expandir el panel -->
    <button 
      class="recorrer-toggle-btn"
      :class="{ 'panel-open': isOpen }"
      @click="$emit('toggle')"
      :title="isOpen ? 'Ocultar panel de pipeline' : 'Recorrer y ver Cómo se procesa el texto'"
    >
      <span class="recorrer-icon">{{ isOpen ? '›' : '‹' }}</span>
      <span v-if="!isOpen" class="vertical-text">COMO SE PROCESA EL TEXTO</span>
    </button>

    <!-- Contenido del Panel Glassmorphism (Imagen 3) -->
    <div class="drawer-inner" v-if="isOpen">
      <!-- Header del Panel -->
      <div class="panel-header">
        <div class="header-left">
          <button class="back-btn" @click="$emit('toggle')" title="Cerrar panel">
            ‹
          </button>
          <div>
            <span class="panel-tag">RIGHT SECTION</span>
            <h3 class="panel-title">NLP Pipeline Glassmorphism Panel</h3>
          </div>
        </div>
        <span class="model-pill">Regresión Logística</span>
      </div>

      <div class="pipeline-intro">
        <div class="pipeline-main-title">CÓMO SE PROCESA EL TEXTO</div>
        <p class="pipeline-subtitle">
          Los mismos pasos que se usaron al entrenar, ejecutados por el pipeline guardado (Fases 1 a 6).
        </p>
      </div>

      <div class="steps-flow">
        <!-- 1. Texto Original -->
        <div class="step-card">
          <div class="step-number-title">
            <span class="step-badge">1</span>
            <h4>Texto Original</h4>
          </div>
          <div class="step-box original-box">
            <p class="step-content original-text">
              "{{ currentAnalysis.textoOriginal || '¿Qué jeans tienen en talla 32 disponibles para envío hoy?' }}"
            </p>
            <div class="step-meta">
              <span>{{ (currentAnalysis.textoOriginal || '').length }} caracteres</span>
              <span>•</span>
              <span>{{ (currentAnalysis.tokens || []).length }} palabras</span>
            </div>
          </div>
        </div>

        <!-- 2. Normalización -->
        <div class="step-card">
          <div class="step-number-title">
            <span class="step-badge">2</span>
            <h4>Normalización</h4>
          </div>
          <p class="step-desc">minúsculas, sin puntuación ni acentos diacríticos</p>
          <div class="step-box norm-box">
            <code class="norm-text">
              {{ currentAnalysis.normalizado || 'que jeans tienen en talla 32 disponibles para envio hoy' }}
            </code>
          </div>
        </div>

        <!-- 3. Tokenización (Con formato { XX XXXX XXXXXXX } solicitado) -->
        <div class="step-card">
          <div class="step-number-title">
            <span class="step-badge">3</span>
            <h4>Tokenización</h4>
          </div>
          <p class="step-desc">División en tokens individuales de dominio</p>
          <div class="step-box token-box">
            <div class="tokens-bracket-wrapper">
              <span class="bracket">{</span>
              <div class="tokens-list">
                <span 
                  v-for="(tok, idx) in (currentAnalysis.tokens || ['que', 'jeans', 'tienen', 'en', 'talla', '32', 'disponibles', 'para', 'envio', 'hoy'])" 
                  :key="idx" 
                  class="token-chip"
                >
                  [ {{ tok }} ]
                </span>
              </div>
              <span class="bracket">}</span>
            </div>
          </div>
        </div>

        <!-- 4. Stop Words -->
        <div class="step-card">
          <div class="step-number-title">
            <span class="step-badge">4</span>
            <h4>Stop Words</h4>
          </div>
          <p class="step-desc">Palabras vacías en español filtradas (se preservan "no", "sin", "más")</p>
          <div class="step-box stopwords-box">
            <div class="stopwords-subgroup">
              <span class="subgroup-label eliminadas">Eliminadas:</span>
              <div class="chips-row">
                <span 
                  v-for="(stop, idx) in (currentAnalysis.stopWords?.eliminadas || ['que', 'en', 'para'])" 
                  :key="idx"
                  class="stop-chip removed"
                >
                  <del>{{ stop }}</del>
                </span>
                <span v-if="!currentAnalysis.stopWords?.eliminadas?.length" class="empty-hint">Ninguna</span>
              </div>
            </div>

            <div class="stopwords-subgroup">
              <span class="subgroup-label conservadas">Se conservan:</span>
              <div class="chips-row">
                <span 
                  v-for="(tok, idx) in (currentAnalysis.stopWords?.conservadas || ['jeans', 'tienen', 'talla', '32', 'disponibles', 'envio', 'hoy'])" 
                  :key="idx"
                  class="stop-chip kept"
                >
                  {{ tok }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 5. Lematización spaCy -->
        <div class="step-card">
          <div class="step-number-title">
            <span class="step-badge">5</span>
            <h4>Lematización spaCy</h4>
          </div>
          <p class="step-desc">Reducción a lemas raíz con es_core_news_sm</p>
          <div class="step-box lemma-box">
            <div class="chips-row">
              <span 
                v-for="(lem, idx) in (currentAnalysis.lematizacion || ['jean', 'tener', 'talla', '32', 'disponible', 'envío', 'hoy'])" 
                :key="idx"
                class="lemma-chip"
              >
                {{ lem }}
              </span>
            </div>
          </div>
        </div>

        <!-- 6. Intención & Modelo ML -->
        <div class="step-card">
          <div class="step-number-title">
            <span class="step-badge">6</span>
            <div class="title-with-pill">
              <h4>Intención &amp; Modelo</h4>
              <span class="confidence-pill">
                Confidence {{ currentAnalysis.clasificacion?.probabilidadPorcentaje || '99.2%' }}
              </span>
            </div>
          </div>
          
          <div class="step-box model-box">
            <div class="winner-row">
              <div class="winner-name">
                <span class="winner-intent">{{ currentAnalysis.clasificacion?.intencion || 'consultar_stock' }}</span>
                <span class="winner-detail">({{ currentAnalysis.clasificacion?.probabilidadPorcentaje || '99.2%' }}) - Regresión Logística</span>
              </div>
            </div>

            <!-- Top 3 Probabilidades con Barras -->
            <div class="top3-container">
              <span class="top3-title">Distribución Top 3:</span>
              <div 
                v-for="item in (currentAnalysis.clasificacion?.top3 || [
                  { intencion: 'consultar_stock', probabilidad: 0.992 },
                  { intencion: 'consultar_tallas', probabilidad: 0.005 },
                  { intencion: 'envios', probabilidad: 0.002 }
                ])" 
                :key="item.intencion"
                class="top3-row"
              >
                <div class="top3-label-row">
                  <span class="top3-name">{{ item.intencion }}</span>
                  <span class="top3-pct">{{ (item.probabilidad * 100).toFixed(1) }}%</span>
                </div>
                <div class="top3-track">
                  <div class="top3-fill" :style="{ width: `${item.probabilidad * 100}%` }"></div>
                </div>
              </div>
            </div>

            <!-- Entidades Extraídas -->
            <div class="extracted-entities-box" v-if="currentAnalysis.entidades">
              <span class="entities-title">Entidades detectadas (Ramiro - Fase 5):</span>
              <div class="entities-chips">
                <span v-if="currentAnalysis.entidades.talla" class="entity-chip">
                  <strong>Talla:</strong> {{ currentAnalysis.entidades.talla }}
                </span>
                <span v-if="currentAnalysis.entidades.categoria" class="entity-chip">
                  <strong>Categoría:</strong> {{ currentAnalysis.entidades.categoria }}
                </span>
                <span v-if="currentAnalysis.entidades.fecha" class="entity-chip">
                  <strong>Envío/Fecha:</strong> {{ currentAnalysis.entidades.fecha }}
                </span>
                <span v-if="currentAnalysis.entidades.color" class="entity-chip">
                  <strong>Color:</strong> {{ currentAnalysis.entidades.color }}
                </span>
              </div>
            </div>

            <!-- Footer Metadatos de Producción -->
            <div class="pipeline-footer-stats">
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
  </aside>
</template>

<script setup>
defineProps({
  isOpen: {
    type: Boolean,
    default: true
  },
  currentAnalysis: {
    type: Object,
    default: () => ({
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
    })
  }
})

defineEmits(['toggle'])
</script>

<style scoped>
.nlp-drawer {
  position: relative;
  width: 440px;
  max-width: 95vw;
  background: rgba(253, 251, 247, 0.92);
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border-left: 1px solid rgba(197, 168, 128, 0.5);
  box-shadow: -12px 0 40px rgba(39, 34, 59, 0.08);
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  z-index: 40;
}

.nlp-drawer:not(.is-open) {
  width: 42px;
  min-width: 42px;
  background: rgba(253, 251, 247, 0.7);
  border-left: 1px solid rgba(197, 168, 128, 0.35);
  cursor: pointer;
}

/* Botón flotante para recorrer "<" */
.recorrer-toggle-btn {
  position: absolute;
  top: 18px;
  left: -22px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #27223b;
  color: #ffffff;
  border: 2px solid #ffffff;
  box-shadow: 0 4px 14px rgba(39, 34, 59, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 50;
  transition: all 0.25s ease;
}

.nlp-drawer:not(.is-open) .recorrer-toggle-btn {
  left: 3px;
  top: 14px;
}

.recorrer-toggle-btn:hover {
  background: #b3884d;
  transform: scale(1.1);
}

.recorrer-icon {
  font-size: 1.35rem;
  font-weight: 700;
  line-height: 1;
}

.vertical-text {
  position: absolute;
  top: 80px;
  left: 10px;
  writing-mode: vertical-rl;
  text-orientation: mixed;
  transform: rotate(180deg);
  font-size: 0.68rem;
  letter-spacing: 0.22em;
  font-weight: 700;
  color: #9c8466;
  white-space: nowrap;
}

/* Inner drawer scroll area */
.drawer-inner {
  padding: 24px 22px;
  overflow-y: auto;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(210, 195, 175, 0.35);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.back-btn {
  background: rgba(39, 34, 59, 0.06);
  border: 1px solid rgba(210, 195, 175, 0.4);
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  font-weight: 700;
  color: #27223b;
  cursor: pointer;
  transition: all 0.2s ease;
}

.back-btn:hover {
  background: #27223b;
  color: #ffffff;
}

.panel-tag {
  font-size: 0.65rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: #9c8466;
  font-weight: 600;
  display: block;
}

.panel-title {
  font-family: var(--font-serif);
  font-size: 1.15rem;
  font-weight: 700;
  color: #1a1816;
}

.model-pill {
  font-size: 0.68rem;
  background: #f4ecdf;
  color: #7b6953;
  padding: 4px 10px;
  border-radius: 999px;
  font-weight: 600;
  border: 1px solid rgba(197, 168, 128, 0.35);
}

.pipeline-intro {
  margin-top: 4px;
}

.pipeline-main-title {
  font-size: 0.92rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: #27223b;
  text-transform: uppercase;
}

.pipeline-subtitle {
  font-size: 0.74rem;
  color: #7b746a;
  margin-top: 2px;
  line-height: 1.4;
}

/* Steps Flow */
.steps-flow {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.step-card {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.step-number-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.step-badge {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #27223b;
  color: #ffffff;
  font-size: 0.72rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-number-title h4 {
  font-size: 0.88rem;
  font-weight: 700;
  color: #1a1816;
}

.title-with-pill {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.confidence-pill {
  font-size: 0.7rem;
  font-weight: 700;
  background: #e8f5e9;
  color: #2e7d32;
  padding: 2px 8px;
  border-radius: 999px;
}

.step-desc {
  font-size: 0.72rem;
  color: #8c8273;
  margin-left: 30px;
}

.step-box {
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid rgba(210, 195, 175, 0.45);
  border-radius: 12px;
  padding: 12px 14px;
  box-shadow: 0 2px 10px rgba(39, 34, 59, 0.03);
  margin-left: 30px;
}

/* 1. Texto Original */
.original-text {
  font-size: 0.86rem;
  font-style: italic;
  color: #2b2824;
  line-height: 1.4;
}

.step-meta {
  display: flex;
  gap: 6px;
  font-size: 0.68rem;
  color: #9e968c;
  margin-top: 6px;
}

/* 2. Normalización */
.norm-text {
  font-family: var(--font-mono);
  font-size: 0.8rem;
  color: #5c3c92;
  display: block;
  word-break: break-word;
  line-height: 1.45;
}

/* 3. Tokenización { [ tok ] [ tok ] } */
.tokens-bracket-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.bracket {
  font-size: 1.3rem;
  font-weight: 300;
  color: #9c8466;
  font-family: var(--font-mono);
}

.tokens-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  flex: 1;
}

.token-chip {
  font-family: var(--font-mono);
  font-size: 0.74rem;
  background: #f7f4ef;
  color: #3b342e;
  padding: 3px 7px;
  border-radius: 6px;
  border: 1px solid rgba(210, 195, 175, 0.4);
}

/* 4. Stop Words */
.stopwords-subgroup {
  margin-bottom: 8px;
}
.stopwords-subgroup:last-child {
  margin-bottom: 0;
}

.subgroup-label {
  font-size: 0.7rem;
  font-weight: 700;
  display: block;
  margin-bottom: 4px;
}
.subgroup-label.eliminadas { color: #c53030; }
.subgroup-label.conservadas { color: #2e7d32; }

.chips-row {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.stop-chip {
  font-family: var(--font-mono);
  font-size: 0.72rem;
  padding: 2px 7px;
  border-radius: 6px;
}

.stop-chip.removed {
  background: #fde8e8;
  color: #c53030;
  border: 1px solid #fecaca;
}

.stop-chip.kept {
  background: #f4ecdf;
  color: #554e46;
  border: 1px solid rgba(197, 168, 128, 0.35);
}

.empty-hint {
  font-size: 0.7rem;
  color: #9e968c;
  font-style: italic;
}

/* 5. Lematización */
.lemma-chip {
  font-family: var(--font-mono);
  font-size: 0.74rem;
  font-weight: 500;
  background: #e8f5e9;
  color: #2e7d32;
  padding: 3px 8px;
  border-radius: 6px;
  border: 1px solid #c8e6c9;
}

/* 6. Intención & Modelo */
.winner-row {
  margin-bottom: 10px;
}

.winner-intent {
  font-size: 0.88rem;
  font-weight: 800;
  color: #27223b;
  font-family: var(--font-mono);
  display: block;
}

.winner-detail {
  font-size: 0.76rem;
  color: #5c3c92;
  font-weight: 600;
}

.top3-container {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(210, 195, 175, 0.3);
}

.top3-title {
  font-size: 0.7rem;
  font-weight: 700;
  color: #635b51;
}

.top3-row {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.top3-label-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.72rem;
  font-family: var(--font-mono);
}

.top3-name {
  color: #3b342e;
}

.top3-pct {
  font-weight: 700;
  color: #27223b;
}

.top3-track {
  width: 100%;
  height: 5px;
  background: #eee8de;
  border-radius: 999px;
  overflow: hidden;
}

.top3-fill {
  height: 100%;
  background: linear-gradient(90deg, #27223b, #5c3c92);
  border-radius: 999px;
}

.extracted-entities-box {
  margin-top: 10px;
  padding-top: 8px;
  border-top: 1px solid rgba(210, 195, 175, 0.3);
}

.entities-title {
  font-size: 0.7rem;
  font-weight: 700;
  color: #635b51;
  display: block;
  margin-bottom: 4px;
}

.entities-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.entity-chip {
  font-size: 0.7rem;
  background: #fdf6ec;
  color: #8c642e;
  padding: 2px 7px;
  border-radius: 5px;
  border: 1px solid #faecd8;
}

.pipeline-footer-stats {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px dashed rgba(210, 195, 175, 0.45);
  font-size: 0.65rem;
  color: #8c8273;
}
</style>

