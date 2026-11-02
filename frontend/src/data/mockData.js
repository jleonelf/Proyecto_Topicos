// Catálogo exclusivo y datos de prueba para Aura Boutique
export const BOUTIQUE_PRODUCTS = [
  {
    id: 1,
    name: "Designer Trench Coat",
    subtitle: "Gabardina Clásica Italiana",
    category: "Abrigos",
    categoryKey: "trench coat",
    priceBs: 890,
    priceUsd: 129,
    stock: 4,
    size: "32 / M",
    color: "Camel / Gabardina",
    image: "https://images.unsplash.com/photo-1544022613-e87ca75a784a?auto=format&fit=crop&w=600&q=80",
    badge: "4 en Stock - Talla 32",
    description: "Confeccionado en algodón hidrófugo con cinturón a tono y botones de cuerno legítimo."
  },
  {
    id: 2,
    name: "Raw Indigo Slim Denim",
    subtitle: "Jeans Selvage Japonés",
    category: "Pantalones",
    categoryKey: "jeans",
    priceBs: 340,
    priceUsd: 49,
    stock: 4,
    size: "32",
    color: "Indigo Oscuro",
    image: "https://images.unsplash.com/photo-1542272604-780c96856592?auto=format&fit=crop&w=600&q=80",
    badge: "4 en Stock - Talla 32",
    description: "Denim de 14 oz con corte slim tailored, teñido natural con añil y remaches de cobre."
  },
  {
    id: 3,
    name: "Organic Linen Shirt",
    subtitle: "Camisa Lino Premium",
    category: "Camisas",
    categoryKey: "camisa",
    priceBs: 290,
    priceUsd: 42,
    stock: 4,
    size: "32 / M",
    color: "Blanco Ópalo",
    image: "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=600&q=80",
    badge: "4 en Stock - Talla 32",
    description: "Fibra 100% lino orgánico europeo, cuello italiano suave y textura ultra respirable."
  },
  {
    id: 4,
    name: "Tailored Double Blazer",
    subtitle: "Saco Sastrería de Lana",
    category: "Blazers",
    categoryKey: "blazer",
    priceBs: 650,
    priceUsd: 95,
    stock: 2,
    size: "40 / L",
    color: "Negro Carbón",
    image: "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?auto=format&fit=crop&w=600&q=80",
    badge: "2 en Stock - Talla 40",
    description: "Silueta estructurada en sarga de lana fría, solapa en pico y forro de seda interior."
  },
  {
    id: 5,
    name: "Pure Cashmere Knit",
    subtitle: "Suéter Cuello Redondo",
    category: "Prendas de Punto",
    categoryKey: "chompa",
    priceBs: 450,
    priceUsd: 65,
    stock: 6,
    size: "M / L",
    color: "Arena / Beige",
    image: "https://images.unsplash.com/photo-1576566588028-4147f3842f27?auto=format&fit=crop&w=600&q=80",
    badge: "Stock Disponible",
    description: "Tejido en punto fino de cachemira mongola de 2 cabos. Suavidad y calidez inigualable."
  },
  {
    id: 6,
    name: "Silk Satin Slip Dress",
    subtitle: "Vestido de Noche en Seda",
    category: "Vestidos",
    categoryKey: "vestido",
    priceBs: 520,
    priceUsd: 75,
    stock: 3,
    size: "S / 36",
    color: "Esmeralda Profundo",
    image: "https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=600&q=80",
    badge: "3 en Stock - Talla S",
    description: "Corte al bies con caída fluida en satén de seda pura, tirantes ajustables ultrafinos."
  }
];

// Preguntas sugeridas para probar el asistente (como en la imagen 1 y 2)
export const PROMPT_PRESETS = [
  {
    label: "Jeans Talla 32 (Imagen 2)",
    text: "¿Qué jeans tienen en talla 32 disponibles para envío hoy?",
    expectedIntent: "consultar_stock",
    tag: "Stock & Envío"
  },
  {
    label: "Consultar Precio",
    text: "¿Cuánto cuesta el trench coat de gabardina?",
    expectedIntent: "consultar_precio",
    tag: "Precios"
  },
  {
    label: "Consultar Tallas",
    text: "¿Qué tallas tienen disponibles de la camisa de lino?",
    expectedIntent: "consultar_tallas",
    tag: "Tallas"
  },
  {
    label: "Envíos a Domicilio",
    text: "¿Hacen envíos a Cochabamba y a provincia?",
    expectedIntent: "envios",
    tag: "Logística"
  },
  {
    label: "Métodos de Pago",
    text: "¿Aceptan transferencias bancarias o cobro QR?",
    expectedIntent: "metodos_pago",
    tag: "Pagos"
  },
  {
    label: "Devoluciones",
    text: "¿Cuál es la política para cambiar una prenda si no me queda?",
    expectedIntent: "devoluciones",
    tag: "Políticas"
  },
  {
    label: "Más Vendidos (Admin)",
    text: "¿Cuáles han sido los productos más vendidos de este mes?",
    expectedIntent: "productos_mas_vendidos",
    tag: "Admin"
  },
  {
    label: "Stock Bajo (Admin)",
    text: "¿Qué productos tienen stock crítico y se están agotando?",
    expectedIntent: "stock_bajo",
    tag: "Admin"
  }
];

export const STORE_INFO = {
  name: "Aura Boutique",
  slogan: "Minimalist Luxury & AI Concierge",
  address: "Av. San Martín #1420, Equipetrol Norte",
  city: "Santa Cruz / La Paz / Cochabamba",
  hours: "Lunes a Sábado de 10:00 a 20:30 · Domingos de 11:00 a 17:00",
  whatsapp: "+591 77012345",
  modelName: "Regresión Logística",
  modelF1: "0.8622",
  modelAccuracy: "0.8606",
  modelLatency: "8.4 ms"
};

