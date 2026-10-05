"""
Carga solo datos de 2016 a Azure SQL.
Borra todo lo anterior y carga limpio.
370 ventas + dimensiones pequeñas = carga rápida.
"""
import pyodbc
import pandas as pd
import getpass
import os

SERVER = "olist-bi-server.database.windows.net"
DATABASE = "olist_bi"
USERNAME = "adminbi"
DATA_DIR = r"C:\PROYECTOS\PowerBI-Business-Intelligence\data\por_anio\2016"

print("=" * 60)
print("CARGA 2016 A AZURE SQL")
print("=" * 60)
PASSWORD = getpass.getpass("Contraseña: ")

print("\nConectando...")
conn_str = (
    f"DRIVER={{ODBC Driver 18 for SQL Server}};"
    f"SERVER={SERVER};DATABASE={DATABASE};"
    f"UID={USERNAME};PWD={PASSWORD};"
    f"Encrypt=yes;TrustServerCertificate=no;"
    f"Connection Timeout=60;"
)
conn = pyodbc.connect(conn_str, timeout=60)
conn.autocommit = True
cursor = conn.cursor()
print("[OK] Conectado\n")

# ============================================================
# PASO 1: Borrar tablas y recrear
# ============================================================
print("PASO 1: Recreando tablas...")

cursor.execute("""
    IF OBJECT_ID('fact_ventas', 'U') IS NOT NULL DROP TABLE fact_ventas;
    IF OBJECT_ID('dim_cliente', 'U') IS NOT NULL DROP TABLE dim_cliente;
    IF OBJECT_ID('dim_vendedor', 'U') IS NOT NULL DROP TABLE dim_vendedor;
    IF OBJECT_ID('dim_producto', 'U') IS NOT NULL DROP TABLE dim_producto;
    IF OBJECT_ID('dim_region', 'U') IS NOT NULL DROP TABLE dim_region;
    IF OBJECT_ID('dim_tiempo', 'U') IS NOT NULL DROP TABLE dim_tiempo;
""")

tablas = [
    """CREATE TABLE dim_tiempo (
        fecha_key INT NOT NULL PRIMARY KEY, fecha DATE NOT NULL,
        dia TINYINT NOT NULL, mes TINYINT NOT NULL, mes_nombre VARCHAR(20) NOT NULL,
        trimestre TINYINT NOT NULL, anio SMALLINT NOT NULL, dia_semana TINYINT NOT NULL,
        dia_semana_nombre VARCHAR(15) NOT NULL, es_fin_semana BIT NOT NULL,
        semana_anio TINYINT NOT NULL, anio_mes VARCHAR(7) NOT NULL, anio_trimestre VARCHAR(7) NOT NULL)""",
    """CREATE TABLE dim_region (
        region_id INT NOT NULL PRIMARY KEY, estado_codigo CHAR(2) NOT NULL,
        estado_nombre VARCHAR(50) NOT NULL, region_nombre VARCHAR(20) NOT NULL,
        ciudad_ejemplo VARCHAR(100) NULL)""",
    """CREATE TABLE dim_producto (
        producto_id INT NOT NULL PRIMARY KEY, producto_original_id VARCHAR(40) NOT NULL,
        categoria_pt VARCHAR(60) NULL, categoria_en VARCHAR(60) NOT NULL,
        peso_g FLOAT NULL, largo_cm FLOAT NULL, alto_cm FLOAT NULL,
        ancho_cm FLOAT NULL, fotos_qty INT NULL)""",
    """CREATE TABLE dim_vendedor (
        vendedor_id INT NOT NULL PRIMARY KEY, vendedor_original_id VARCHAR(40) NOT NULL,
        ciudad VARCHAR(100) NOT NULL, estado_codigo CHAR(2) NOT NULL,
        region_id INT NOT NULL,
        CONSTRAINT FK_vendedor_region FOREIGN KEY (region_id) REFERENCES dim_region(region_id))""",
    """CREATE TABLE dim_cliente (
        cliente_id INT NOT NULL PRIMARY KEY, cliente_unique_id VARCHAR(40) NOT NULL,
        ciudad VARCHAR(100) NOT NULL, estado_codigo CHAR(2) NOT NULL,
        region_id INT NOT NULL, segmento VARCHAR(30) NOT NULL, total_pedidos INT NOT NULL DEFAULT 1,
        CONSTRAINT FK_cliente_region FOREIGN KEY (region_id) REFERENCES dim_region(region_id))""",
    """CREATE TABLE fact_ventas (
        venta_id INT NOT NULL PRIMARY KEY, order_id VARCHAR(40) NOT NULL,
        fecha_key INT NOT NULL, producto_id INT NOT NULL, cliente_id INT NOT NULL,
        vendedor_id INT NOT NULL, cantidad INT NOT NULL DEFAULT 1,
        precio DECIMAL(10,2) NOT NULL, flete DECIMAL(10,2) NOT NULL,
        valor_total DECIMAL(10,2) NOT NULL, metodo_pago VARCHAR(30) NULL,
        cuotas_pago INT NULL, review_score TINYINT NULL, order_status VARCHAR(20) NOT NULL,
        dias_entrega_real INT NULL, dias_entrega_estimado INT NULL, entrega_a_tiempo BIT NULL,
        CONSTRAINT FK_venta_tiempo FOREIGN KEY (fecha_key) REFERENCES dim_tiempo(fecha_key),
        CONSTRAINT FK_venta_producto FOREIGN KEY (producto_id) REFERENCES dim_producto(producto_id),
        CONSTRAINT FK_venta_cliente FOREIGN KEY (cliente_id) REFERENCES dim_cliente(cliente_id),
        CONSTRAINT FK_venta_vendedor FOREIGN KEY (vendedor_id) REFERENCES dim_vendedor(vendedor_id))""",
]

for sql in tablas:
    cursor.execute(sql)
print("[OK] Tablas creadas\n")

# ============================================================
# PASO 2: Cargar datos de 2016
# ============================================================
print("PASO 2: Cargando datos de 2016...")

def cargar(tabla, csv_file, columnas):
    path = os.path.join(DATA_DIR, csv_file)
    df = pd.read_csv(path)
    df = df[columnas]
    placeholders = ", ".join(["?" for _ in columnas])
    col_names = ", ".join(columnas)
    sql = f"INSERT INTO {tabla} ({col_names}) VALUES ({placeholders})"
    rows = []
    for _, row in df.iterrows():
        fila = []
        for v in row:
            if pd.isna(v):
                fila.append(None)
            elif isinstance(v, float) and v == int(v):
                fila.append(int(v))
            else:
                fila.append(v)
        rows.append(tuple(fila))
    cursor.executemany(sql, rows)
    print(f"  {tabla:<20} {len(rows):>6,} filas [OK]")
    return len(rows)

cargar("dim_tiempo", "dim_tiempo.csv",
    ['fecha_key','fecha','dia','mes','mes_nombre','trimestre','anio',
     'dia_semana','dia_semana_nombre','es_fin_semana','semana_anio',
     'anio_mes','anio_trimestre'])

cargar("dim_region", "dim_region.csv",
    ['region_id','estado_codigo','estado_nombre','region_nombre','ciudad_ejemplo'])

cargar("dim_producto", "dim_producto.csv",
    ['producto_id','producto_original_id','categoria_pt','categoria_en',
     'peso_g','largo_cm','alto_cm','ancho_cm','fotos_qty'])

cargar("dim_vendedor", "dim_vendedor.csv",
    ['vendedor_id','vendedor_original_id','ciudad','estado_codigo','region_id'])

cargar("dim_cliente", "dim_cliente.csv",
    ['cliente_id','cliente_unique_id','ciudad','estado_codigo',
     'region_id','segmento','total_pedidos'])

cargar("fact_ventas", "fact_ventas.csv",
    ['venta_id','order_id','fecha_key','producto_id','cliente_id',
     'vendedor_id','cantidad','precio','flete','valor_total',
     'metodo_pago','cuotas_pago','review_score','order_status',
     'dias_entrega_real','dias_entrega_estimado','entrega_a_tiempo'])

# ============================================================
# PASO 3: Validación
# ============================================================
print("\n" + "=" * 60)
print("VALIDACION")
print("=" * 60)

for tabla in ['dim_tiempo','dim_region','dim_producto','dim_vendedor','dim_cliente','fact_ventas']:
    cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
    print(f"  {tabla:<20} {cursor.fetchone()[0]:>6,} filas")

cursor.execute("SELECT MIN(fecha_key), MAX(fecha_key) FROM fact_ventas")
row = cursor.fetchone()
print(f"\n  Rango de fechas: {row[0]} -> {row[1]}")

cursor.execute("SELECT SUM(precio) FROM fact_ventas")
total = cursor.fetchone()[0]
print(f"  Ingreso total 2016: R$ {total:,.2f}")

conn.close()
print("\n[OK] 2016 CARGADO EXITOSAMENTE")
print("Ya puedes conectar Power BI a esta base de datos.")
