-- ============================================================
-- STAR SCHEMA - Retail Business Intelligence (Olist E-Commerce)
-- Target: Azure SQL Database
-- Dataset: Brazilian E-Commerce Public Dataset by Olist
-- ============================================================

-- Orden de eliminacion (respetar dependencias FK)
IF OBJECT_ID('fact_ventas', 'U') IS NOT NULL DROP TABLE fact_ventas;
IF OBJECT_ID('dim_cliente', 'U') IS NOT NULL DROP TABLE dim_cliente;
IF OBJECT_ID('dim_vendedor', 'U') IS NOT NULL DROP TABLE dim_vendedor;
IF OBJECT_ID('dim_producto', 'U') IS NOT NULL DROP TABLE dim_producto;
IF OBJECT_ID('dim_region', 'U') IS NOT NULL DROP TABLE dim_region;
IF OBJECT_ID('dim_tiempo', 'U') IS NOT NULL DROP TABLE dim_tiempo;
GO

-- ============================================================
-- Dimension: Tiempo (Date)
-- ============================================================
CREATE TABLE dim_tiempo (
    fecha_key           INT           NOT NULL PRIMARY KEY,  -- YYYYMMDD
    fecha               DATE          NOT NULL,
    dia                 TINYINT       NOT NULL,
    mes                 TINYINT       NOT NULL,
    mes_nombre          VARCHAR(20)   NOT NULL,
    trimestre           TINYINT       NOT NULL,
    anio                SMALLINT      NOT NULL,
    dia_semana          TINYINT       NOT NULL,  -- 0=Lunes, 6=Domingo
    dia_semana_nombre   VARCHAR(15)   NOT NULL,
    es_fin_semana       BIT           NOT NULL,
    semana_anio         TINYINT       NOT NULL,
    anio_mes            VARCHAR(7)    NOT NULL,  -- '2017-01'
    anio_trimestre      VARCHAR(7)    NOT NULL   -- '2017-Q1'
);

-- ============================================================
-- Dimension: Region (Estados de Brasil)
-- ============================================================
CREATE TABLE dim_region (
    region_id           INT           NOT NULL PRIMARY KEY,
    estado_codigo       CHAR(2)       NOT NULL,  -- SP, RJ, MG...
    estado_nombre       VARCHAR(50)   NOT NULL,
    region_nombre       VARCHAR(20)   NOT NULL,  -- Sudeste, Sur, Nordeste, Norte, Centro-Oeste
    ciudad_ejemplo      VARCHAR(100)  NULL
);

-- ============================================================
-- Dimension: Producto
-- ============================================================
CREATE TABLE dim_producto (
    producto_id         INT           NOT NULL PRIMARY KEY,
    producto_original_id VARCHAR(40)  NOT NULL,  -- hash original de Olist
    categoria_pt        VARCHAR(60)   NULL,       -- nombre original en portugues
    categoria_en        VARCHAR(60)   NOT NULL,   -- traducido al ingles
    peso_g              FLOAT         NULL,
    largo_cm            FLOAT         NULL,
    alto_cm             FLOAT         NULL,
    ancho_cm            FLOAT         NULL,
    fotos_qty           INT           NULL
);

-- ============================================================
-- Dimension: Vendedor (Seller = Tienda en Olist marketplace)
-- ============================================================
CREATE TABLE dim_vendedor (
    vendedor_id         INT           NOT NULL PRIMARY KEY,
    vendedor_original_id VARCHAR(40)  NOT NULL,
    ciudad              VARCHAR(100)  NOT NULL,
    estado_codigo       CHAR(2)       NOT NULL,
    region_id           INT           NOT NULL,
    CONSTRAINT FK_vendedor_region FOREIGN KEY (region_id) REFERENCES dim_region(region_id)
);

-- ============================================================
-- Dimension: Cliente
-- ============================================================
CREATE TABLE dim_cliente (
    cliente_id          INT           NOT NULL PRIMARY KEY,
    cliente_unique_id   VARCHAR(40)   NOT NULL,
    ciudad              VARCHAR(100)  NOT NULL,
    estado_codigo       CHAR(2)       NOT NULL,
    region_id           INT           NOT NULL,
    segmento            VARCHAR(30)   NOT NULL,  -- Frecuente, Ocasional, Unico
    total_pedidos       INT           NOT NULL DEFAULT 1,
    CONSTRAINT FK_cliente_region FOREIGN KEY (region_id) REFERENCES dim_region(region_id)
);

-- ============================================================
-- Fact: Ventas (cada linea de pedido es un registro)
-- ============================================================
CREATE TABLE fact_ventas (
    venta_id            INT           NOT NULL PRIMARY KEY,
    order_id            VARCHAR(40)   NOT NULL,
    fecha_key           INT           NOT NULL,
    producto_id         INT           NOT NULL,
    cliente_id          INT           NOT NULL,
    vendedor_id         INT           NOT NULL,
    cantidad            INT           NOT NULL DEFAULT 1,
    precio              DECIMAL(10,2) NOT NULL,
    flete               DECIMAL(10,2) NOT NULL,
    valor_total         DECIMAL(10,2) NOT NULL,  -- precio + flete
    metodo_pago         VARCHAR(30)   NULL,
    cuotas_pago         INT           NULL,
    review_score        TINYINT       NULL,       -- 1-5
    order_status        VARCHAR(20)   NOT NULL,
    dias_entrega_real   INT           NULL,       -- dias desde compra hasta entrega
    dias_entrega_estimado INT        NULL,       -- dias estimados
    entrega_a_tiempo    BIT           NULL,       -- 1=a tiempo, 0=tarde
    CONSTRAINT FK_venta_tiempo    FOREIGN KEY (fecha_key)    REFERENCES dim_tiempo(fecha_key),
    CONSTRAINT FK_venta_producto  FOREIGN KEY (producto_id)  REFERENCES dim_producto(producto_id),
    CONSTRAINT FK_venta_cliente   FOREIGN KEY (cliente_id)   REFERENCES dim_cliente(cliente_id),
    CONSTRAINT FK_venta_vendedor  FOREIGN KEY (vendedor_id)  REFERENCES dim_vendedor(vendedor_id)
);

-- ============================================================
-- Indices para performance en Power BI (Direct Query / Import)
-- ============================================================
CREATE NONCLUSTERED INDEX IX_fact_ventas_fecha      ON fact_ventas(fecha_key);
CREATE NONCLUSTERED INDEX IX_fact_ventas_producto   ON fact_ventas(producto_id);
CREATE NONCLUSTERED INDEX IX_fact_ventas_cliente    ON fact_ventas(cliente_id);
CREATE NONCLUSTERED INDEX IX_fact_ventas_vendedor   ON fact_ventas(vendedor_id);
CREATE NONCLUSTERED INDEX IX_fact_ventas_status     ON fact_ventas(order_status);
CREATE NONCLUSTERED INDEX IX_fact_ventas_fecha_prod ON fact_ventas(fecha_key, producto_id);
