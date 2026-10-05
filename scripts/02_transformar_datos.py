"""
Transformacion de datos: Olist Raw CSVs -> Star Schema CSVs
Resuelve problemas reales de calidad de datos:
  - Nulos en categorias de producto (610 registros)
  - Nulos en fechas de entrega (2,965 registros)
  - Nombres de categoria en portugues -> ingles
  - IDs hash -> IDs numericos secuenciales
  - Creacion de segmentos de cliente por comportamiento de compra
  - Generacion de dimension tiempo completa
"""
import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

RAW_DIR = r"C:\PROYECTOS\PowerBI-Business-Intelligence\data\raw"
OUT_DIR = r"C:\PROYECTOS\PowerBI-Business-Intelligence\data\transformed"
os.makedirs(OUT_DIR, exist_ok=True)

print("=" * 60)
print("FASE 1: Carga de datos crudos")
print("=" * 60)

orders = pd.read_csv(os.path.join(RAW_DIR, "olist_orders_dataset.csv"))
items = pd.read_csv(os.path.join(RAW_DIR, "olist_order_items_dataset.csv"))
products = pd.read_csv(os.path.join(RAW_DIR, "olist_products_dataset.csv"))
customers = pd.read_csv(os.path.join(RAW_DIR, "olist_customers_dataset.csv"))
sellers = pd.read_csv(os.path.join(RAW_DIR, "olist_sellers_dataset.csv"))
payments = pd.read_csv(os.path.join(RAW_DIR, "olist_order_payments_dataset.csv"))
reviews = pd.read_csv(os.path.join(RAW_DIR, "olist_order_reviews_dataset.csv"))
cat_translation = pd.read_csv(os.path.join(RAW_DIR, "product_category_name_translation.csv"))

print(f"  Orders:    {len(orders):>8,} filas")
print(f"  Items:     {len(items):>8,} filas")
print(f"  Products:  {len(products):>8,} filas")
print(f"  Customers: {len(customers):>8,} filas")
print(f"  Sellers:   {len(sellers):>8,} filas")
print(f"  Payments:  {len(payments):>8,} filas")
print(f"  Reviews:   {len(reviews):>8,} filas")

# ============================================================
# FASE 2: Limpieza de datos
# ============================================================
print("\n" + "=" * 60)
print("FASE 2: Limpieza de datos")
print("=" * 60)

# 2.1 Convertir fechas (string -> datetime)
date_cols_orders = [
    'order_purchase_timestamp', 'order_approved_at',
    'order_delivered_carrier_date', 'order_delivered_customer_date',
    'order_estimated_delivery_date'
]
for col in date_cols_orders:
    orders[col] = pd.to_datetime(orders[col], errors='coerce')
print(f"  [OK] Fechas convertidas a datetime ({len(date_cols_orders)} columnas)")

# 2.2 Manejar nulos en categorias de producto
nulos_cat_antes = products['product_category_name'].isnull().sum()
products['product_category_name'] = products['product_category_name'].fillna('sem_categoria')
# Agregar la traduccion para 'sem_categoria'
cat_translation = pd.concat([
    cat_translation,
    pd.DataFrame([{'product_category_name': 'sem_categoria',
                   'product_category_name_english': 'uncategorized'}])
], ignore_index=True)
print(f"  [OK] {nulos_cat_antes} productos sin categoria -> 'uncategorized'")

# 2.3 Traducir categorias al ingles
products = products.merge(cat_translation, on='product_category_name', how='left')
# Verificar si quedaron sin traducir
sin_traducir = products['product_category_name_english'].isnull().sum()
if sin_traducir > 0:
    # Categorias que no estaban en la tabla de traduccion
    cats_faltantes = products[products['product_category_name_english'].isnull()]['product_category_name'].unique()
    print(f"  [WARN] {sin_traducir} productos con categorias sin traduccion: {cats_faltantes}")
    products['product_category_name_english'] = products['product_category_name_english'].fillna(
        products['product_category_name']
    )
print(f"  [OK] Categorias traducidas al ingles")

# 2.4 Manejar nulos en dimensiones de producto
for col in ['product_weight_g', 'product_length_cm', 'product_height_cm', 'product_width_cm']:
    nulos = products[col].isnull().sum()
    if nulos > 0:
        mediana = products[col].median()
        products[col] = products[col].fillna(mediana)
        print(f"  [OK] {col}: {nulos} nulos -> mediana ({mediana:.0f})")

# 2.5 Filtrar solo ordenes entregadas o enviadas (para analisis de ventas)
status_counts = orders['order_status'].value_counts()
print(f"\n  Status de ordenes:")
for status, count in status_counts.items():
    print(f"    {status}: {count:,}")

# Mantener todas las ordenes pero marcar el status
print(f"  [OK] Manteniendo todas las ordenes con su status")

# ============================================================
# FASE 3: Construccion de dimensiones
# ============================================================
print("\n" + "=" * 60)
print("FASE 3: Construccion de dimensiones")
print("=" * 60)

# --- dim_tiempo ---
print("\n  Construyendo dim_tiempo...")
fecha_min = orders['order_purchase_timestamp'].min().date()
fecha_max = orders['order_purchase_timestamp'].max().date()
print(f"    Rango: {fecha_min} -> {fecha_max}")

fechas = pd.date_range(start=fecha_min, end=fecha_max, freq='D')

dias_semana_es = {0: 'Lunes', 1: 'Martes', 2: 'Miercoles', 3: 'Jueves',
                  4: 'Viernes', 5: 'Sabado', 6: 'Domingo'}
meses_es = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}

dim_tiempo = pd.DataFrame({
    'fecha_key': [int(f.strftime('%Y%m%d')) for f in fechas],
    'fecha': fechas.date,
    'dia': fechas.day,
    'mes': fechas.month,
    'mes_nombre': [meses_es[m] for m in fechas.month],
    'trimestre': fechas.quarter,
    'anio': fechas.year,
    'dia_semana': fechas.dayofweek,
    'dia_semana_nombre': [dias_semana_es[d] for d in fechas.dayofweek],
    'es_fin_semana': (fechas.dayofweek >= 5).astype(int),
    'semana_anio': fechas.isocalendar().week.values,
    'anio_mes': [f.strftime('%Y-%m') for f in fechas],
    'anio_trimestre': [f"{f.year}-Q{(f.month - 1) // 3 + 1}" for f in fechas],
})
print(f"    [OK] {len(dim_tiempo)} dias generados")

# --- dim_region ---
print("\n  Construyendo dim_region...")
estados_brasil = {
    'AC': ('Acre', 'Norte'), 'AL': ('Alagoas', 'Nordeste'),
    'AM': ('Amazonas', 'Norte'), 'AP': ('Amapa', 'Norte'),
    'BA': ('Bahia', 'Nordeste'), 'CE': ('Ceara', 'Nordeste'),
    'DF': ('Distrito Federal', 'Centro-Oeste'), 'ES': ('Espirito Santo', 'Sudeste'),
    'GO': ('Goias', 'Centro-Oeste'), 'MA': ('Maranhao', 'Nordeste'),
    'MG': ('Minas Gerais', 'Sudeste'), 'MS': ('Mato Grosso do Sul', 'Centro-Oeste'),
    'MT': ('Mato Grosso', 'Centro-Oeste'), 'PA': ('Para', 'Norte'),
    'PB': ('Paraiba', 'Nordeste'), 'PE': ('Pernambuco', 'Nordeste'),
    'PI': ('Piaui', 'Nordeste'), 'PR': ('Parana', 'Sur'),
    'RJ': ('Rio de Janeiro', 'Sudeste'), 'RN': ('Rio Grande do Norte', 'Nordeste'),
    'RO': ('Rondonia', 'Norte'), 'RR': ('Roraima', 'Norte'),
    'RS': ('Rio Grande do Sul', 'Sur'), 'SC': ('Santa Catarina', 'Sur'),
    'SE': ('Sergipe', 'Nordeste'), 'SP': ('Sao Paulo', 'Sudeste'),
    'TO': ('Tocantins', 'Norte'),
}

# Obtener estados unicos de clientes y vendedores
estados_usados = set(customers['customer_state'].unique()) | set(sellers['seller_state'].unique())

dim_region_rows = []
for i, (codigo, (nombre, region)) in enumerate(estados_brasil.items(), 1):
    if codigo in estados_usados:
        dim_region_rows.append({
            'region_id': i,
            'estado_codigo': codigo,
            'estado_nombre': nombre,
            'region_nombre': region,
            'ciudad_ejemplo': None
        })

dim_region = pd.DataFrame(dim_region_rows)

# Agregar ciudad mas comun por estado
for idx, row in dim_region.iterrows():
    estado = row['estado_codigo']
    ciudades = customers[customers['customer_state'] == estado]['customer_city']
    if len(ciudades) > 0:
        dim_region.at[idx, 'ciudad_ejemplo'] = ciudades.mode().iloc[0]

# Crear mapeo estado -> region_id
estado_region_map = dict(zip(dim_region['estado_codigo'], dim_region['region_id']))
print(f"    [OK] {len(dim_region)} estados/regiones")

# --- dim_producto ---
print("\n  Construyendo dim_producto...")
dim_producto = products[['product_id', 'product_category_name', 'product_category_name_english',
                          'product_weight_g', 'product_length_cm', 'product_height_cm',
                          'product_width_cm', 'product_photos_qty']].copy()

# Solo productos que aparecen en items (evitar productos huerfanos)
productos_usados = items['product_id'].unique()
dim_producto = dim_producto[dim_producto['product_id'].isin(productos_usados)].copy()

dim_producto = dim_producto.reset_index(drop=True)
dim_producto['producto_id_num'] = dim_producto.index + 1

# Mapeo hash -> numerico
producto_id_map = dict(zip(dim_producto['product_id'], dim_producto['producto_id_num']))

dim_producto_final = pd.DataFrame({
    'producto_id': dim_producto['producto_id_num'],
    'producto_original_id': dim_producto['product_id'],
    'categoria_pt': dim_producto['product_category_name'],
    'categoria_en': dim_producto['product_category_name_english'],
    'peso_g': dim_producto['product_weight_g'],
    'largo_cm': dim_producto['product_length_cm'],
    'alto_cm': dim_producto['product_height_cm'],
    'ancho_cm': dim_producto['product_width_cm'],
    'fotos_qty': dim_producto['product_photos_qty'].fillna(0).astype(int),
})
print(f"    [OK] {len(dim_producto_final)} productos (de {len(products)} originales, filtrados a usados)")

# --- dim_vendedor ---
print("\n  Construyendo dim_vendedor...")
vendedores_usados = items['seller_id'].unique()
sellers_filtrado = sellers[sellers['seller_id'].isin(vendedores_usados)].copy()
sellers_filtrado = sellers_filtrado.reset_index(drop=True)
sellers_filtrado['vendedor_id_num'] = sellers_filtrado.index + 1

vendedor_id_map = dict(zip(sellers_filtrado['seller_id'], sellers_filtrado['vendedor_id_num']))

dim_vendedor = pd.DataFrame({
    'vendedor_id': sellers_filtrado['vendedor_id_num'],
    'vendedor_original_id': sellers_filtrado['seller_id'],
    'ciudad': sellers_filtrado['seller_city'],
    'estado_codigo': sellers_filtrado['seller_state'],
    'region_id': sellers_filtrado['seller_state'].map(estado_region_map),
})

# Manejar vendedores de estados no mapeados
nulos_region = dim_vendedor['region_id'].isnull().sum()
if nulos_region > 0:
    print(f"    [WARN] {nulos_region} vendedores con estado no mapeado")
    dim_vendedor['region_id'] = dim_vendedor['region_id'].fillna(1).astype(int)
else:
    dim_vendedor['region_id'] = dim_vendedor['region_id'].astype(int)

print(f"    [OK] {len(dim_vendedor)} vendedores")

# --- dim_cliente ---
print("\n  Construyendo dim_cliente...")

# Contar pedidos por cliente unico para segmentacion
customer_orders = orders.merge(customers[['customer_id', 'customer_unique_id']], on='customer_id')
orders_per_customer = customer_orders.groupby('customer_unique_id').size().reset_index(name='total_pedidos')

# Segmentacion por frecuencia de compra
def segmentar_cliente(n_pedidos):
    if n_pedidos >= 3:
        return 'Frecuente'
    elif n_pedidos == 2:
        return 'Ocasional'
    else:
        return 'Unico'

orders_per_customer['segmento'] = orders_per_customer['total_pedidos'].apply(segmentar_cliente)

print(f"    Segmentacion de clientes:")
for seg, count in orders_per_customer['segmento'].value_counts().items():
    print(f"      {seg}: {count:,}")

# Construir dimension cliente (por customer_id, no unique_id, para mantener relacion con orders)
customers_enriched = customers.merge(
    orders_per_customer, on='customer_unique_id', how='left'
)
customers_enriched['total_pedidos'] = customers_enriched['total_pedidos'].fillna(1).astype(int)
customers_enriched['segmento'] = customers_enriched['segmento'].fillna('Unico')

customers_enriched = customers_enriched.reset_index(drop=True)
customers_enriched['cliente_id_num'] = customers_enriched.index + 1

cliente_id_map = dict(zip(customers_enriched['customer_id'], customers_enriched['cliente_id_num']))

dim_cliente = pd.DataFrame({
    'cliente_id': customers_enriched['cliente_id_num'],
    'cliente_unique_id': customers_enriched['customer_unique_id'],
    'ciudad': customers_enriched['customer_city'],
    'estado_codigo': customers_enriched['customer_state'],
    'region_id': customers_enriched['customer_state'].map(estado_region_map),
    'segmento': customers_enriched['segmento'],
    'total_pedidos': customers_enriched['total_pedidos'],
})

nulos_region_cli = dim_cliente['region_id'].isnull().sum()
if nulos_region_cli > 0:
    print(f"    [WARN] {nulos_region_cli} clientes con estado no mapeado")
    dim_cliente['region_id'] = dim_cliente['region_id'].fillna(1).astype(int)
else:
    dim_cliente['region_id'] = dim_cliente['region_id'].astype(int)

print(f"    [OK] {len(dim_cliente)} clientes")

# ============================================================
# FASE 4: Construccion de tabla de hechos
# ============================================================
print("\n" + "=" * 60)
print("FASE 4: Construccion de fact_ventas")
print("=" * 60)

# Unir items con orders
fact = items.merge(orders[['order_id', 'customer_id', 'order_status',
                           'order_purchase_timestamp', 'order_delivered_customer_date',
                           'order_estimated_delivery_date']],
                   on='order_id', how='inner')

print(f"  Items + Orders: {len(fact):,} filas")

# Agregar payment info (tomar el metodo de pago principal por order)
payment_principal = payments.sort_values('payment_value', ascending=False) \
    .drop_duplicates(subset='order_id', keep='first')[['order_id', 'payment_type', 'payment_installments']]
fact = fact.merge(payment_principal, on='order_id', how='left')
print(f"  + Pagos: {len(fact):,} filas")

# Agregar reviews (puede haber pedidos sin review)
review_principal = reviews.drop_duplicates(subset='order_id', keep='first')[['order_id', 'review_score']]
fact = fact.merge(review_principal, on='order_id', how='left')
print(f"  + Reviews: {len(fact):,} filas")

# Calcular metricas de entrega
fact['dias_entrega_real'] = (
    fact['order_delivered_customer_date'] - fact['order_purchase_timestamp']
).dt.days
fact['dias_entrega_estimado'] = (
    fact['order_estimated_delivery_date'] - fact['order_purchase_timestamp']
).dt.days
fact['entrega_a_tiempo'] = np.where(
    fact['order_delivered_customer_date'].isnull(), None,
    np.where(fact['order_delivered_customer_date'] <= fact['order_estimated_delivery_date'], 1, 0)
)

# Crear fecha_key
fact['fecha_key'] = fact['order_purchase_timestamp'].dt.strftime('%Y%m%d').astype(int)

# Mapear IDs
fact['producto_id_num'] = fact['product_id'].map(producto_id_map)
fact['cliente_id_num'] = fact['customer_id'].map(cliente_id_map)
fact['vendedor_id_num'] = fact['seller_id'].map(vendedor_id_map)

# Verificar mapeos fallidos
for col, nombre in [('producto_id_num', 'producto'), ('cliente_id_num', 'cliente'), ('vendedor_id_num', 'vendedor')]:
    nulos = fact[col].isnull().sum()
    if nulos > 0:
        print(f"  [WARN] {nulos} filas sin mapeo de {nombre} -> eliminadas")
        fact = fact.dropna(subset=[col])

fact['valor_total'] = fact['price'] + fact['freight_value']

# Construir tabla final
fact_ventas = pd.DataFrame({
    'venta_id': range(1, len(fact) + 1),
    'order_id': fact['order_id'].values,
    'fecha_key': fact['fecha_key'].values,
    'producto_id': fact['producto_id_num'].astype(int).values,
    'cliente_id': fact['cliente_id_num'].astype(int).values,
    'vendedor_id': fact['vendedor_id_num'].astype(int).values,
    'cantidad': fact['order_item_id'].values,  # item sequence within order
    'precio': fact['price'].values,
    'flete': fact['freight_value'].values,
    'valor_total': fact['valor_total'].values,
    'metodo_pago': fact['payment_type'].values,
    'cuotas_pago': fact['payment_installments'].values,
    'review_score': fact['review_score'].values,
    'order_status': fact['order_status'].values,
    'dias_entrega_real': fact['dias_entrega_real'].values,
    'dias_entrega_estimado': fact['dias_entrega_estimado'].values,
    'entrega_a_tiempo': fact['entrega_a_tiempo'].values,
})

# Corregir: cantidad debe ser 1 por linea de item (order_item_id es el secuencial)
fact_ventas['cantidad'] = 1

print(f"\n  [OK] fact_ventas: {len(fact_ventas):,} filas")
print(f"  Rango de fechas: {fact_ventas['fecha_key'].min()} -> {fact_ventas['fecha_key'].max()}")

# ============================================================
# FASE 5: Validacion
# ============================================================
print("\n" + "=" * 60)
print("FASE 5: Validacion de integridad referencial")
print("=" * 60)

# Verificar que todos los FK de fact existen en dimensiones
for fk_col, dim_df, dim_pk, dim_name in [
    ('fecha_key', dim_tiempo, 'fecha_key', 'dim_tiempo'),
    ('producto_id', dim_producto_final, 'producto_id', 'dim_producto'),
    ('cliente_id', dim_cliente, 'cliente_id', 'dim_cliente'),
    ('vendedor_id', dim_vendedor, 'vendedor_id', 'dim_vendedor'),
]:
    fk_values = set(fact_ventas[fk_col].unique())
    pk_values = set(dim_df[dim_pk].unique())
    huerfanos = fk_values - pk_values
    if huerfanos:
        print(f"  [ERROR] {len(huerfanos)} valores huerfanos en {fk_col} (no existen en {dim_name})")
    else:
        print(f"  [OK] {fk_col} -> {dim_name}: integridad OK")

# ============================================================
# FASE 6: Exportar CSVs transformados
# ============================================================
print("\n" + "=" * 60)
print("FASE 6: Exportar CSVs")
print("=" * 60)

dim_tiempo.to_csv(os.path.join(OUT_DIR, 'dim_tiempo.csv'), index=False)
print(f"  dim_tiempo.csv       -> {len(dim_tiempo):>8,} filas")

dim_region.to_csv(os.path.join(OUT_DIR, 'dim_region.csv'), index=False)
print(f"  dim_region.csv       -> {len(dim_region):>8,} filas")

dim_producto_final.to_csv(os.path.join(OUT_DIR, 'dim_producto.csv'), index=False)
print(f"  dim_producto.csv     -> {len(dim_producto_final):>8,} filas")

dim_vendedor.to_csv(os.path.join(OUT_DIR, 'dim_vendedor.csv'), index=False)
print(f"  dim_vendedor.csv     -> {len(dim_vendedor):>8,} filas")

dim_cliente.to_csv(os.path.join(OUT_DIR, 'dim_cliente.csv'), index=False)
print(f"  dim_cliente.csv      -> {len(dim_cliente):>8,} filas")

fact_ventas.to_csv(os.path.join(OUT_DIR, 'fact_ventas.csv'), index=False)
print(f"  fact_ventas.csv      -> {len(fact_ventas):>8,} filas")

print("\n" + "=" * 60)
print("TRANSFORMACION COMPLETADA")
print("=" * 60)
print(f"\nArchivos en: {OUT_DIR}")
