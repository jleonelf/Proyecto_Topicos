<template>
  <div class="app-root">
    <!-- Top Navigation Header with Window Mockup Bar -->
    <Navbar 
      :active-tab="currentTab"
      :is-api-connected="isApiOnline"
      @select-tab="handleSelectTab"
      @open-metrics="showMetricsModal = true"
      @toggle-drawer="toggleDrawer"
    />

    <!-- Main Workspace Layout: LEFT (Catalog), CENTER (Assistant), RIGHT (NLP Pipeline) -->
    <main class="main-layout" :class="{ 'drawer-expanded': isDrawerOpen }">
      <!-- LEFT SECTION: Luxury Catalog Grid -->
      <section class="left-section">
        <CatalogGrid 
          :highlighted-product-id="highlightedProductId"
          @ask-product="handleProductQuery"
        />
      </section>

      <!-- CENTER SECTION: Floating Luxury VIP Voice & Chat Assistant -->
      <section class="center-section">
        <ChatAssistant 
          ref="assistantRef"
          :latest-analysis="currentAnalysis"
          :is-processing="isProcessing"
          @send-message="handleUserMessage"
          @toggle-drawer="toggleDrawer"
        />
      </section>

      <!-- RIGHT SECTION: NLP Pipeline Glassmorphism Panel (con botón de recorrer "<") -->
      <NlpPipelineDrawer 
        :is-open="isDrawerOpen"
        :current-analysis="currentAnalysis"
        @toggle="toggleDrawer"
      />
    </main>

    <!-- Metrics Modal (Datos reales de artifacts/metricas.json) -->
    <AdminMetricsModal 
      v-if="showMetricsModal"
      @close="showMetricsModal = false"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Navbar from './components/Navbar.vue'
import CatalogGrid from './components/CatalogGrid.vue'
import ChatAssistant from './components/ChatAssistant.vue'
import NlpPipelineDrawer from './components/NlpPipelineDrawer.vue'
import AdminMetricsModal from './components/AdminMetricsModal.vue'
import { procesarConsultaNLP } from './utils/nlpSimulator.js'
import { enviarMensajeChat, verificarSaludApi } from './api/client.js'

const currentTab = ref('coleccion')
const isDrawerOpen = ref(true) // Abierto por defecto para mostrar el pipeline tal como en la Imagen 3
const showMetricsModal = ref(false)
const isProcessing = ref(false)
const isApiOnline = ref(false)
const highlightedProductId = ref(2) // Raw Denim por defecto (Imagen 2)

const assistantRef = ref(null)

// Análisis inicial: Exactamente la consulta de la Imagen 2 & 3
const currentAnalysis = ref(
  procesarConsultaNLP('¿Qué jeans tienen en talla 32 disponibles para envío hoy?')
)

onMounted(async () => {
  // Verificar si la API FastAPI está levantada en localhost:8000
  const health = await verificarSaludApi()
  if (health && health.estado === 'activo') {
    isApiOnline.value = true
  }
})

function toggleDrawer() {
  isDrawerOpen.value = !isDrawerOpen.value
}

function handleSelectTab(tab) {
  currentTab.value = tab
  if (tab === 'metricas') {
    showMetricsModal.value = true
  }
}

async function handleUserMessage(texto) {
  isProcessing.value = true

  try {
    // Invocar cliente API (con fallback inmediato al motor NLP local)
    const result = await enviarMensajeChat(texto, 'cliente')
    
    // Actualizar el estado global del análisis de NLP para el Drawer y la tarjeta
    currentAnalysis.value = result.pasos

    // Vincular con el catálogo si se detecta producto
    if (result.entidades && result.entidades.categoria) {
      const cat = result.entidades.categoria.toLowerCase()
      if (cat.includes('jean')) highlightedProductId.value = 2
      else if (cat.includes('trench') || cat.includes('abrigo')) highlightedProductId.value = 1
      else if (cat.includes('lino') || cat.includes('camisa')) highlightedProductId.value = 3
      else if (cat.includes('blazer')) highlightedProductId.value = 4
      else if (cat.includes('punto') || cat.includes('cashmere')) highlightedProductId.value = 5
      else if (cat.includes('vestido') || cat.includes('seda')) highlightedProductId.value = 6
    }

    // Agregar respuesta en el componente de chat
    if (assistantRef.value) {
      assistantRef.value.addAssistantReply(result.respuesta)
    }
  } catch (err) {
    console.error('Error al procesar mensaje:', err)
  } finally {
    isProcessing.value = false
  }
}

function handleProductQuery(product) {
  const query = `¿Tienen disponible el ${product.name} en ${product.size} para envío?`
  if (assistantRef.value) {
    assistantRef.value.setInput(query)
  }
  highlightedProductId.value = product.id
  handleUserMessage(query)
}
</script>

<style scoped>
.app-root {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--bg-canvas);
}

.main-layout {
  display: flex;
  flex-direction: column;
  flex: 1;
  max-width: 1680px;
  width: 100%;
  margin: 0 auto;
  padding: 24px;
  gap: 24px;
  position: relative;
}

@media (min-width: 1024px) {
  .main-layout {
    display: grid;
    grid-template-columns: 1fr 480px auto;
    align-items: start;
    gap: 24px;
  }
}

.left-section {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.center-section {
  display: flex;
  flex-direction: column;
  position: sticky;
  top: 92px;
}

@media (max-width: 1023px) {
  .center-section {
    position: static;
  }
}
</style>

