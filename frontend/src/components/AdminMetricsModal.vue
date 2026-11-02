<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-card glass-panel fade-in">
      <div class="modal-header">
        <div>
          <span class="modal-tag">EVALUACIÓN &amp; ML METRICS</span>
          <h2 class="modal-title">Métricas de Producción del Modelo</h2>
          <p class="modal-subtitle">Resultados oficiales generados en artifacts/metricas.json (Jorge - Fase 6)</p>
        </div>
        <button class="close-btn" @click="$emit('close')">✕</button>
      </div>

    </div>
  </div>
</template>

<script setup>
defineEmits(['close'])

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
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(30, 26, 42, 0.6);
  backdrop-filter: blur(8px);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.modal-card {
  width: 820px;
  max-width: 95vw;
  max-height: 90vh;
  background: rgba(255, 255, 255, 0.96);
  border-radius: 24px;
  border: 1px solid rgba(210, 195, 175, 0.6);
  box-shadow: 0 25px 60px rgba(39, 34, 59, 0.25);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px 28px;
  border-bottom: 1px solid rgba(210, 195, 175, 0.35);
  background: #fdfbf7;
}

.modal-tag {
  font-size: 0.68rem;
  letter-spacing: 0.16em;
  font-weight: 700;
  color: #9c8466;
  text-transform: uppercase;
}

.modal-title {
  font-family: var(--font-serif);
  font-size: 1.55rem;
  font-weight: 700;
  color: #1a1816;
  margin-top: 2px;
}

.modal-subtitle {
  font-size: 0.78rem;
  color: #7b746a;
}

.close-btn {
  background: rgba(39, 34, 59, 0.08);
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  color: #27223b;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #27223b;
  color: #ffffff;
}

.modal-body {
  padding: 24px 28px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 12px;
}

.kpi-card {
  background: #f7f4ef;
  border: 1px solid rgba(210, 195, 175, 0.4);
  border-radius: 14px;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.kpi-card.winner {
  background: #27223b;
  color: white;
  border-color: #27223b;
}

.kpi-card.winner .kpi-label { color: #d1a9ff; }
.kpi-card.winner .kpi-value { color: #ffffff; }
.kpi-card.winner .kpi-sub { color: #b2c9ff; }

.kpi-label {
  font-size: 0.7rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  font-weight: 600;
  color: #7b746a;
}

.kpi-value {
  font-size: 1.25rem;
  font-weight: 700;
  font-family: var(--font-mono);
  color: #1a1816;
}

.kpi-sub {
  font-size: 0.68rem;
  color: #9c8466;
}

.section-title {
  font-size: 0.88rem;
  font-weight: 700;
  color: #1a1816;
  margin-bottom: 8px;
}

.table-wrapper {
  overflow-x: auto;
  border-radius: 10px;
  border: 1px solid rgba(210, 195, 175, 0.4);
}

.metrics-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

.metrics-table th {
  background: #f4ecdf;
  padding: 10px 14px;
  text-align: left;
  font-weight: 600;
  color: #5c4a32;
  border-bottom: 1px solid rgba(210, 195, 175, 0.4);
}

.metrics-table td {
  padding: 10px 14px;
  border-bottom: 1px solid rgba(210, 195, 175, 0.25);
}

.highlight-row {
  background: rgba(197, 168, 128, 0.12);
}

.status-tag {
  font-size: 0.68rem;
  padding: 3px 8px;
  border-radius: 999px;
  font-weight: 600;
}

.status-tag.active {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-tag.bench {
  background: #ebf8ff;
  color: #2b6cb0;
}

.status-tag.baseline {
  background: #edf2f7;
  color: #4a5568;
}

.intents-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.intent-cloud-chip {
  font-size: 0.72rem;
  background: #f4ecdf;
  color: #4a453f;
  padding: 4px 10px;
  border-radius: 8px;
  border: 1px solid rgba(210, 195, 175, 0.4);
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.intent-cloud-chip.admin {
  background: #edf2f7;
  color: #2d3748;
}

.role-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #b3884d;
}
.role-dot.admin {
  background: #5c3c92;
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 28px;
  border-top: 1px solid rgba(210, 195, 175, 0.35);
  background: #fdfbf7;
}

.footer-note {
  font-size: 0.72rem;
  color: #8c8273;
}

.primary-btn {
  background: #27223b;
  color: white;
  border: none;
  padding: 8px 20px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.primary-btn:hover {
  background: #b3884d;
}
</style>

