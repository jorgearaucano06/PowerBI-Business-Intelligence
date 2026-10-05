"""
Carga incremental de 2016 a Azure SQL.
NO borra tablas ni datos de otros años.
Solo inserta 2016, ignorando duplicados en dimensiones.
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
print("CARGA INCREMENTAL 2016 A AZURE SQL")
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
# PASO 1: Limpiar solo datos de 2016
# ============================================================
print("PASO 1: Limpiando datos de 2016...")
cursor.execute("DELETE FROM fact_ventas WHERE fecha_key >= 20160101 AND fecha_key <= 20161231")
print(f"  fact_ventas 2016 eliminadas")
cursor.execute("DELETE FROM dim_tiempo WHERE fecha_key >= 20160101 AND fecha_key <= 20161231")
print(f"  dim_tiempo 2016 eliminadas")
print("[OK]\n")

# ============================================================
# PASO 2: Funciones de carga
# ============================================================
def preparar_fila(row):
    """Convierte NaN a None y floats enteros a int."""
    fila = []
    for v in row:
        if pd.isna(v):
            fila.append(None)
        elif isinstance(v, float) and v == int(v):
            fila.append(int(v))
        else:
            fila.append(v)
    return tuple(fila)

def cargar_directo(tabla, csv_file, columnas):
    """INSERT directo, para tablas sin riesgo de duplicados."""
    path = os.path.join(DATA_DIR, csv_file)
    df = pd.read_csv(path)[columnas]
    placeholders = ", ".join(["?" for _ in columnas])
    col_names = ", ".join(columnas)
    sql = f"INSERT INTO {tabla} ({col_names}) VALUES ({placeholders})"
    rows = [preparar_fila(row) for _, row in df.iterrows()]
    cursor.executemany(sql, rows)
    print(f"  {tabla:<20} {len(rows):>6,} filas [OK]")

def cargar_upsert(tabla, csv_file, columnas, pk):
    """INSERT ignorando duplicados por PK."""
    path = os.path.join(DATA_DIR, csv_file)
    df = pd.read_csv(path)[columnas]
    insertadas = 0
    ignoradas = 0
    placeholders = ", ".join(["?" for _ in columnas])
    col_names = ", ".join(columnas)
    sql = f"INSERT INTO {tabla} ({col_names}) VALUES ({placeholders})"
    for _, row in df.iterrows():
        fila = preparar_fila(row)
        try:
            cursor.execute(sql, fila)
            insertadas += 1
        except pyodbc.IntegrityError:
            ignoradas += 1
    print(f"  {tabla:<20} {insertadas:>6,} nuevas, {ignoradas:>4,} existentes [OK]")

# ============================================================
# PASO 3: Cargar datos de 2016
# ============================================================
print("PASO 2: Cargando datos de 2016...")

cargar_directo("dim_tiempo", "dim_tiempo.csv",
    ['fecha_key','fecha','dia','mes','mes_nombre','trimestre','anio',
     'dia_semana','dia_semana_nombre','es_fin_semana','semana_anio',
     'anio_mes','anio_trimestre'])

cargar_upsert("dim_region", "dim_region.csv",
    ['region_id','estado_codigo','estado_nombre','region_nombre','ciudad_ejemplo'],
    'region_id')

cargar_upsert("dim_producto", "dim_producto.csv",
    ['producto_id','producto_original_id','categoria_pt','categoria_en',
     'peso_g','largo_cm','alto_cm','ancho_cm','fotos_qty'],
    'producto_id')

cargar_upsert("dim_vendedor", "dim_vendedor.csv",
    ['vendedor_id','vendedor_original_id','ciudad','estado_codigo','region_id'],
    'vendedor_id')

cargar_upsert("dim_cliente", "dim_cliente.csv",
    ['cliente_id','cliente_unique_id','ciudad','estado_codigo',
     'region_id','segmento','total_pedidos'],
    'cliente_id')

cargar_directo("fact_ventas", "fact_ventas.csv",
    ['venta_id','order_id','fecha_key','producto_id','cliente_id',
     'vendedor_id','cantidad','precio','flete','valor_total',
     'metodo_pago','cuotas_pago','review_score','order_status',
     'dias_entrega_real','dias_entrega_estimado','entrega_a_tiempo'])

# ============================================================
# PASO 4: Validación
# ============================================================
print("\n" + "=" * 60)
print("VALIDACION (todos los años)")
print("=" * 60)

for tabla in ['dim_tiempo','dim_region','dim_producto','dim_vendedor','dim_cliente','fact_ventas']:
    cursor.execute(f"SELECT COUNT(*) FROM {tabla}")
    print(f"  {tabla:<20} {cursor.fetchone()[0]:>6,} filas")

cursor.execute("SELECT MIN(fecha_key), MAX(fecha_key) FROM fact_ventas")
row = cursor.fetchone()
print(f"\n  Rango de fechas: {row[0]} -> {row[1]}")

cursor.execute("SELECT anio, COUNT(*) as ventas, SUM(precio) as ingresos FROM fact_ventas f JOIN dim_tiempo t ON f.fecha_key = t.fecha_key GROUP BY anio ORDER BY anio")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]:>6,} ventas, R$ {row[2]:>12,.2f}")

conn.close()
print("\n[OK] 2016 CARGADO EXITOSAMENTE (sin afectar otros años)")
