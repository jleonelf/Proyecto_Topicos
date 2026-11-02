import React, { useState, useMemo } from 'react'
import ProductCard from './ProductCard.jsx'
import { BOUTIQUE_PRODUCTS } from '../data/mockData.js'

export default function CatalogGrid({
  highlightedProductId = null,
  onAskProduct
}) {
  const [selectedCategory, setSelectedCategory] = useState('Todos')
  const categories = ['Todos', 'Abrigos', 'Pantalones', 'Camisas', 'Blazers', 'Prendas de Punto']

  const filteredProducts = useMemo(() => {
    if (selectedCategory === 'Todos') return BOUTIQUE_PRODUCTS
    return BOUTIQUE_PRODUCTS.filter(p => p.category === selectedCategory)
  }, [selectedCategory])

  return (
    <section className="catalog-section">
      <div className="catalog-header">
        <div>
          <h2 className="section-title">Luxury Boutique Live Inventory</h2>
          <p className="section-desc">Catálogo en tiempo real con integración directa a clasificación de intenciones y stock.</p>
        </div>

        {/* Category Filter Pills */}
        <div className="filter-pills">
          {categories.map(cat => (
            <button 
              key={cat}
              type="button"
              className={`pill-btn ${selectedCategory === cat ? 'active' : ''}`}
              onClick={() => setSelectedCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Products Grid */}
      <div className="products-grid">
        {filteredProducts.map(item => (
          <ProductCard 
            key={item.id} 
            product={item}
            isSelected={highlightedProductId === item.id}
            onAskProduct={onAskProduct}
          />
        ))}
      </div>
    </section>
  )
}

