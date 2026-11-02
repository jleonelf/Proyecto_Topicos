import React from 'react'

export default function ProductCard({
  product,
  isSelected = false,
  onAskProduct
}) {
  return (
    <div className={`product-card ${isSelected ? 'is-selected' : ''}`}>
      <div className="image-wrapper">
        <img src={product.image} alt={product.name} className="product-image" loading="lazy" />
        <div className="stock-badge">
          <span className="stock-dot"></span>
          {product.badge}
        </div>
        <button 
          type="button"
          className="quick-ask-btn"
          onClick={(e) => {
            e.stopPropagation()
            onAskProduct && onAskProduct(product)
          }}
          title="Consultar al Concierge sobre esta prenda"
        >
          <span>Consultar</span>
        </button>
      </div>

      <div className="product-details">
        <div className="category-tag">{product.category}</div>
        <h3 className="product-title">{product.name}</h3>
        <p className="product-subtitle">{product.subtitle}</p>
        
        <div className="product-footer">
          <div className="price-container">
            <span className="price-currency">Precio:</span>
            <span className="price-amount">{product.priceBs} Bs</span>
            <span className="price-usd">(${product.priceUsd})</span>
          </div>
          <div className="size-pill">
            {product.size}
          </div>
        </div>
      </div>
    </div>
  )
}

