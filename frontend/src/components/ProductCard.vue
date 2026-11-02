<template>
  <div class="product-card" :class="{ 'is-selected': isSelected }">
    <div class="image-wrapper">
      <img :src="product.image" :alt="product.name" class="product-image" loading="lazy" />
      <div class="stock-badge">
        <span class="stock-dot"></span>
        {{ product.badge }}
      </div>
      <button 
        class="quick-ask-btn"
        @click.stop="$emit('ask-product', product)"
        title="Consultar al Concierge sobre esta prenda"
      >
        <span>Consultar</span>
      </button>
    </div>

    <div class="product-details">
      <div class="category-tag">{{ product.category }}</div>
      <h3 class="product-title">{{ product.name }}</h3>
      <p class="product-subtitle">{{ product.subtitle }}</p>
      
      <div class="product-footer">
        <div class="price-container">
          <span class="price-currency">Precio:</span>
          <span class="price-amount">{{ product.priceBs }} Bs</span>
          <span class="price-usd">(${{ product.priceUsd }})</span>
        </div>
        <div class="size-pill">
          {{ product.size }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  product: {
    type: Object,
    required: true
  },
  isSelected: {
    type: Boolean,
    default: false
  }
})

defineEmits(['ask-product'])
</script>

<style scoped>
.product-card {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  border-radius: 18px;
  overflow: hidden;
  border: 1px solid rgba(210, 195, 175, 0.4);
  box-shadow: 0 4px 20px rgba(39, 34, 59, 0.04);
  transition: all 0.35s cubic-bezier(0.16, 1, 0.3, 1);
  display: flex;
  flex-direction: column;
}

.product-card:hover {
  transform: translateY(-5px);
  border-color: rgba(197, 168, 128, 0.8);
  box-shadow: 0 12px 30px rgba(39, 34, 59, 0.09);
}

.product-card.is-selected {
  border-color: #b3884d;
  box-shadow: 0 0 0 2px rgba(179, 136, 77, 0.3), 0 12px 32px rgba(39, 34, 59, 0.12);
}

.image-wrapper {
  position: relative;
  width: 100%;
  aspect-ratio: 4 / 4.6;
  background: #eee8e0;
  overflow: hidden;
}

.product-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

.product-card:hover .product-image {
  transform: scale(1.04);
}

.stock-badge {
  position: absolute;
  bottom: 10px;
  left: 10px;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 5px;
  border: 1px solid rgba(210, 195, 175, 0.5);
}

.stock-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #2e7d32;
}

.quick-ask-btn {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(39, 34, 59, 0.85);
  backdrop-filter: blur(8px);
  color: white;
  border: none;
  border-radius: 999px;
  padding: 5px 12px;
  font-size: 0.72rem;
  font-weight: 500;
  cursor: pointer;
  opacity: 0;
  transform: translateY(-4px);
  transition: all 0.25s ease;
}

.product-card:hover .quick-ask-btn {
  opacity: 1;
  transform: translateY(0);
}

.quick-ask-btn:hover {
  background: #b3884d;
}

.product-details {
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  flex: 1;
}

.category-tag {
  font-size: 0.68rem;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #9c8466;
  font-weight: 600;
  margin-bottom: 2px;
}

.product-title {
  font-family: var(--font-serif);
  font-size: 1.12rem;
  font-weight: 600;
  color: #1a1816;
  line-height: 1.25;
}

.product-subtitle {
  font-size: 0.75rem;
  color: #7b746a;
  margin-top: 2px;
  margin-bottom: 12px;
}

.product-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
  padding-top: 8px;
  border-top: 1px solid rgba(210, 195, 175, 0.25);
}

.price-container {
  display: flex;
  align-items: baseline;
  gap: 5px;
}

.price-currency {
  font-size: 0.75rem;
  color: #666;
}

.price-amount {
  font-size: 0.95rem;
  font-weight: 700;
  color: #1a1816;
}

.price-usd {
  font-size: 0.72rem;
  color: #8c8273;
}

.size-pill {
  font-size: 0.72rem;
  font-weight: 500;
  padding: 2px 8px;
  background: #f4ecdf;
  color: #7b6953;
  border-radius: 6px;
  border: 1px solid rgba(197, 168, 128, 0.3);
}
</style>

