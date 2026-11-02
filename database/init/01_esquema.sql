-- Esquema de la base de datos de la tienda (formato estándar de importación, plan sección 3.2).
-- PostgreSQL ejecuta este archivo automáticamente la primera vez que se crea el contenedor db.

-- productos.csv: sku, nombre, categoria, talla, color, precio, stock
-- Cada sku es una variante concreta (prenda + talla + color).
CREATE TABLE IF NOT EXISTS productos (
    sku        VARCHAR(50)    PRIMARY KEY,
    nombre     VARCHAR(200)   NOT NULL,
    categoria  VARCHAR(100)   NOT NULL,
    talla      VARCHAR(20),
    color      VARCHAR(50),
    precio     NUMERIC(10, 2) NOT NULL CHECK (precio >= 0),
    stock      INTEGER        NOT NULL DEFAULT 0 CHECK (stock >= 0)
);

-- ventas.csv: fecha (YYYY-MM-DD), sku, cantidad, precio_unitario
CREATE TABLE IF NOT EXISTS ventas (
    id               SERIAL         PRIMARY KEY,
    fecha            DATE           NOT NULL,
    sku              VARCHAR(50)    NOT NULL REFERENCES productos (sku),
    cantidad         INTEGER        NOT NULL CHECK (cantidad > 0),
    precio_unitario  NUMERIC(10, 2) NOT NULL CHECK (precio_unitario >= 0)
);

CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas (fecha);
CREATE INDEX IF NOT EXISTS idx_ventas_sku ON ventas (sku);

-- tienda.json: nombre, direccion, horarios, envios, devoluciones, metodos_pago
-- Una sola fila por tienda importada; los campos con estructura libre van en JSONB.
CREATE TABLE IF NOT EXISTS tienda (
    id            SMALLINT     PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    nombre        VARCHAR(200) NOT NULL,
    direccion     TEXT,
    horarios      JSONB,
    envios        JSONB,
    devoluciones  JSONB,
    metodos_pago  JSONB
);
