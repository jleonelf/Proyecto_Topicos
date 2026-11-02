# Aura Boutique — AI Concierge & NLP Pipeline Frontend (React 18 + Vite)

Frontend interactivo desarrollado con **React 18** y **Vite**, diseñado específicamente para el proyecto de **Asistente para Tiendas de Ropa** según el `PLAN_DE_TRABAJO.md`.

Inspirado en el diseño editorial de lujo (Imagen 2) y el desglose pedagógico paso a paso del pipeline de NLP (Imagen 3).

---

## 🌟 Características Principales

1. **Diseño Editorial de Lujo (Aura Boutique Concierge)**
   - Paleta tonal neutra de alta gama: Marfil cálido, obsidian y detalles champagne/dorados.
   - Orbe iridiscente 3D flotante con animación líquida y respuesta a estados de voz y procesamiento.
   - Barra superior estilo navegador Safari con tabs de navegación (`[Colección 2026]`, `[Inventario & Métricas]`).

2. **Botón de Recorrer `<` y Panel Desplegable ("CÓMO SE PROCESA EL TEXTO")**
   - Panel lateral glassmorphism retráctil que se abre/cierra suavemente con el botón `‹` / `›`.
   - **1. Texto Original**: Muestra la consulta recibida con conteo de caracteres y palabras.
   - **2. Normalización**: Minúsculas, eliminación de signos de puntuación y tildes.
   - **3. Tokenización**: Formato exacto `{ [ tok1 ] [ tok2 ] [ tok3 ] }` con chips visuales de cada token léxico.
   - **4. Stop Words**: Visualización clara de palabras vacías eliminadas (en rojo tachado) vs conservadas (preservando "no", "sin", "más").
   - **5. Lematización spaCy**: Reducción morfológica a lemas raíz con chips verdes suaves (`jean`, `tener`, `talla`, `disponible`, `envío`).
   - **6. Intención & Modelo ML**: 
     - Modelo y métricas reales: pendiente de unir con Jorge (Fase 6).
     - Confianza calibrada (ej. **99.2%**).
     - Desglose de probabilidades Top 3 con barras animadas.
     - Extracción de entidades detectadas (`[Talla: 32]`, `[Categoría: Jeans]`, `[Envío: Hoy]`).

3. **Interacción por Voz & Texto**
   - Dictado por micrófono usando **Web Speech API** (`SpeechRecognition`).
   - Lectura de respuestas habladas con síntesis de voz (`SpeechSynthesis`).
   - Botones rápidos de prueba con frases del dominio:
     - *Jeans Talla 32 (Imagen 2)*
     - *Consultar Precios*
     - *Tallas Disponibles*
     - *Envíos a Domicilio*
     - *Métodos de Pago QR*
     - *Devoluciones y Garantía*
     - *Reportes y Métricas (Admin)*

4. **Integración Dual (API FastAPI o Modo Autónomo)**
   - Detecta automáticamente si el backend FastAPI está activo en `http://localhost:8000`.
   - Si el backend no está corriendo, utiliza su **motor NLP cliente integrado** sin interrumpir la experiencia.

---

## 🚀 Cómo Ejecutar el Frontend

### Requisitos
- Node.js (v18 o superior)
- npm

### 1. Iniciar en modo desarrollo
```bash
cd frontend
npm install
npm run dev
```
La aplicación estará disponible inmediatamente en:
👉 **`http://localhost:5173`**

### 2. Compilar para producción
```bash
cd frontend
npm run build
```
Genera la carpeta optimizada `dist/`.
