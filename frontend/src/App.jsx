import React, { useState, useEffect, useRef } from 'react'
import Navbar from './components/Navbar.jsx'
import CatalogGrid from './components/CatalogGrid.jsx'
import ChatAssistant from './components/ChatAssistant.jsx'
import NlpPipelineDrawer from './components/NlpPipelineDrawer.jsx'
import AdminMetricsModal from './components/AdminMetricsModal.jsx'
import InventarioMetricas from './components/InventarioMetricas.jsx'
import { procesarConsultaNLP } from './utils/nlpSimulator.js'
import { enviarMensajeChat, verificarSaludApi } from './api/client.js'

export default function App() {
  const [currentTab, setCurrentTab] = useState('coleccion')
  const [isDrawerOpen, setIsDrawerOpen] = useState(true)
  const [showMetricsModal, setShowMetricsModal] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const [isApiOnline, setIsApiOnline] = useState(false)
  const [highlightedProductId, setHighlightedProductId] = useState(2) // Raw Denim por defecto (Imagen 2)

  const assistantRef = useRef(null)

  // Análisis inicial: Exactamente la consulta de la Imagen 2 & 3
  const [currentAnalysis, setCurrentAnalysis] = useState(() => 
    procesarConsultaNLP('¿Qué jeans tienen en talla 32 disponibles para envío hoy?')
  )

  useEffect(() => {
    // Verificar si la API FastAPI está levantada en localhost:8000
    async function checkApi() {
      const health = await verificarSaludApi()
      if (health && health.estado === 'activo') {
        setIsApiOnline(true)
      }
    }
    checkApi()
  }, [])

  function toggleDrawer() {
    setIsDrawerOpen(prev => !prev)
  }

  function handleSelectTab(tab) {
    // 'metricas' ya no abre un modal: cambia toda la vista al apartado "Inventarios y métricas"
    setCurrentTab(tab)
  }

  async function handleUserMessage(texto) {
    setIsProcessing(true)

    try {
      // Invocar cliente API (con fallback automático al motor NLP cliente)
      const result = await enviarMensajeChat(texto, 'cliente')
      
      // Actualizar el estado global del análisis de NLP para el Drawer y la tarjeta
      setCurrentAnalysis(result.pasos)

      // Vincular con el catálogo si se detecta producto
      if (result.entidades && result.entidades.categoria) {
        const cat = result.entidades.categoria.toLowerCase()
        if (cat.includes('jean')) setHighlightedProductId(2)
        else if (cat.includes('trench') || cat.includes('abrigo')) setHighlightedProductId(1)
        else if (cat.includes('lino') || cat.includes('camisa')) setHighlightedProductId(3)
        else if (cat.includes('blazer')) setHighlightedProductId(4)
        else if (cat.includes('punto') || cat.includes('cashmere')) setHighlightedProductId(5)
        else if (cat.includes('vestido') || cat.includes('seda')) setHighlightedProductId(6)
      }

      // Agregar respuesta en el componente de chat
      if (assistantRef.current) {
        assistantRef.current.addAssistantReply(result.respuesta)
      }
    } catch (err) {
      console.error('Error al procesar mensaje:', err)
    } finally {
      setIsProcessing(false)
    }
  }

  function handleProductQuery(product) {
    const query = `¿Tienen disponible el ${product.name} en ${product.size} para envío?`
    if (assistantRef.current) {
      assistantRef.current.setInput(query)
    }
    setHighlightedProductId(product.id)
    handleUserMessage(query)
  }

  return (
    <div className="app-root">
      {/* Top Navigation Header with Window Mockup Bar */}
      <Navbar 
        activeTab={currentTab}
        isApiConnected={isApiOnline}
        onSelectTab={handleSelectTab}
        onOpenMetrics={() => handleSelectTab('metricas')}
        onToggleDrawer={toggleDrawer}
      />

      {/* Apartado "Inventarios y métricas": reemplaza las tres columnas del asistente */}
      {currentTab === 'metricas' && (
        <InventarioMetricas onVolver={() => handleSelectTab('coleccion')} />
      )}

      {/* Main Workspace Layout: LEFT (Catalog), CENTER (Assistant), RIGHT (NLP Pipeline) */}
      {/* Se oculta con "hidden" (no se desmonta) para conservar la conversación del chat */}
      <main className={`main-layout ${isDrawerOpen ? 'drawer-expanded' : ''}`} hidden={currentTab === 'metricas'}>
        {/* LEFT SECTION: Luxury Catalog Grid */}
        <section className="left-section">
          <CatalogGrid 
            highlightedProductId={highlightedProductId}
            onAskProduct={handleProductQuery}
          />
        </section>

        {/* CENTER SECTION: Floating Luxury VIP Voice & Chat Assistant */}
        <section className="center-section">
          <ChatAssistant 
            ref={assistantRef}
            latestAnalysis={currentAnalysis}
            isProcessing={isProcessing}
            onSendMessage={handleUserMessage}
            onToggleDrawer={toggleDrawer}
          />
        </section>

        {/* RIGHT SECTION: NLP Pipeline Glassmorphism Panel (con botón de recorrer "<") */}
        <NlpPipelineDrawer 
          isOpen={isDrawerOpen}
          currentAnalysis={currentAnalysis}
          onToggle={toggleDrawer}
        />
      </main>

      {/* Metrics Modal (Datos reales de artifacts/metricas.json) */}
      {showMetricsModal && (
        <AdminMetricsModal 
          onClose={() => setShowMetricsModal(false)}
        />
      )}
    </div>
  )
}

