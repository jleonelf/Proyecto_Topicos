<template>
  <section class="catalog-section">
    <div class="catalog-header">
      <div>
        <h2 class="section-title">Luxury Boutique Live Inventory</h2>
        <p class="section-desc">Catálogo en tiempo real con integración directa a clasificación de intenciones y stock.</p>
      </div>

      <!-- Category Filter Pills -->
      <div class="filter-pills">
        <button 
          v-for="cat in categories" 
          :key="cat"
          class="pill-btn"
          :class="{ active: selectedCategory === cat }"
          @click="selectedCategory = cat"
        >
          {{ cat }}
        </button>
      </div>
    </div>

    <!-- Products Grid -->
    <div class="products-grid">
      <ProductCard 
        v-for="item in filteredProducts" 
        :key="item.id" 
        :product="item"
        :is-selected="highlightedProductId === item.id"
        @ask-product="$emit('ask-product', $event)"
      />
    </div>
  </section>
</template>

<script setup>
import { ref, computed } from 'vue'
import ProductCard from './ProductCard.vue'
import { BOUTIQUE_PRODUCTS } from '../data/mockData.js'

const props = defineProps({
  highlightedProductId: {
    type: Number,
    default: null
  }
})

defineEmits(['ask-product'])

const selectedCategory = ref('Todos')

const categories = ['Todos', 'Abrigos', 'Pantalones', 'Camisas', 'Blazers', 'Prendas de Punto']

const filteredProducts = computed(() => {
  if (selectedCategory.value === 'Todos') return BOUTIQUE_PRODUCTS
  return BOUTIQUE_PRODUCTS.filter(p => p.category === selectedCategory.value)
})
</script>

<style scoped>
.catalog-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.catalog-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

@media (min-width: 900px) {
  .catalog-header {
    flex-direction: row;
    align-items: flex-end;
    justify-content: space-between;
  }
}

.section-title {
  font-family: var(--font-serif);
  font-size: 1.7rem;
  font-weight: 600;
  color: #1a1816;
  letter-spacing: -0.01em;
}

.section-desc {
  font-size: 0.82rem;
  color: #7b746a;
  margin-top: 2px;
}

.filter-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pill-btn {
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid rgba(210, 195, 175, 0.4);
  padding: 5px 14px;
  border-radius: 999px;
  font-size: 0.78rem;
  color: #635b51;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s ease;
}

.pill-btn:hover {
  background: rgba(197, 168, 128, 0.15);
  color: #1a1816;
  border-color: #b3884d;
}

.pill-btn.active {
  background: #27223b;
  color: #ffffff;
  border-color: #27223b;
  box-shadow: 0 2px 8px rgba(39, 34, 59, 0.2);
}

.products-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 18px;
}
</style>

