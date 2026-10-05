"""
Divide los datos transformados por año.
Crea carpetas separadas para cada año:
  data/por_anio/2016/  → Para cargar con Python
  data/por_anio/2017/  → Para cargar con Azure Data Factory
  data/por_anio/2018/  → Para trigger automático de ADF
"""
import pandas as pd
import os

TRANSFORMED_DIR = r"C:\PROYECTOS\PowerBI-Business-Intelligence\data\transformed"
OUTPUT_DIR = r"C:\PROYECTOS\PowerBI-Business-Intelligence\data\por_anio"

print("=" * 60)
print("DIVIDIENDO DATOS POR AÑO")
print("=" * 60)

# Leer fact_ventas y dim_tiempo para saber el año de cada venta
fact = pd.read_csv(os.path.join(TRANSFORMED_DIR, "fact_ventas.csv"))
dim_tiempo = pd.read_csv(os.path.join(TRANSFORMED_DIR, "dim_tiempo.csv"))

# Extraer año del fecha_key (YYYYMMDD)
fact['anio'] = fact['fecha_key'].astype(str).str[:4].astype(int)

print(f"\nDistribución de fact_ventas por año:")
for anio, count in fact['anio'].value_counts().sort_index().items():
    print(f"  {anio}: {count:,} ventas")

# Leer todas las dimensiones
dim_region = pd.read_csv(os.path.join(TRANSFORMED_DIR, "dim_region.csv"))
dim_producto = pd.read_csv(os.path.join(TRANSFORMED_DIR, "dim_producto.csv"))
dim_vendedor = pd.read_csv(os.path.join(TRANSFORMED_DIR, "dim_vendedor.csv"))
dim_cliente = pd.read_csv(os.path.join(TRANSFORMED_DIR, "dim_cliente.csv"))

# Para cada año, crear carpeta y guardar:
# - Las dimensiones COMPLETAS (son tablas de referencia, se cargan enteras)
# - Solo las ventas de ese año
for anio in [2016, 2017, 2018]:
    anio_dir = os.path.join(OUTPUT_DIR, str(anio))
    os.makedirs(anio_dir, exist_ok=True)

    # Fact ventas filtrado por año
    fact_anio = fact[fact['anio'] == anio].drop(columns=['anio'])
    fact_anio.to_csv(os.path.join(anio_dir, "fact_ventas.csv"), index=False)

    # Dimensiones: solo las que se usan en las ventas de este año
    # dim_tiempo: solo fechas de este año
    fechas_usadas = fact_anio['fecha_key'].unique()
    dt_anio = dim_tiempo[dim_tiempo['fecha_key'].isin(fechas_usadas)]
    dt_anio.to_csv(os.path.join(anio_dir, "dim_tiempo.csv"), index=False)

    # dim_producto: solo productos vendidos este año
    prods_usados = fact_anio['producto_id'].unique()
    dp_anio = dim_producto[dim_producto['producto_id'].isin(prods_usados)]
    dp_anio.to_csv(os.path.join(anio_dir, "dim_producto.csv"), index=False)

    # dim_vendedor: solo vendedores activos este año
    vend_usados = fact_anio['vendedor_id'].unique()
    dv_anio = dim_vendedor[dim_vendedor['vendedor_id'].isin(vend_usados)]
    dv_anio.to_csv(os.path.join(anio_dir, "dim_vendedor.csv"), index=False)

    # dim_cliente: solo clientes que compraron este año
    cli_usados = fact_anio['cliente_id'].unique()
    dc_anio = dim_cliente[dim_cliente['cliente_id'].isin(cli_usados)]
    dc_anio.to_csv(os.path.join(anio_dir, "dim_cliente.csv"), index=False)

    # dim_region: todas (son solo 27, tabla pequeña de referencia)
    dim_region.to_csv(os.path.join(anio_dir, "dim_region.csv"), index=False)

    print(f"\n  {anio}/")
    print(f"    fact_ventas.csv   {len(fact_anio):>8,} filas")
    print(f"    dim_tiempo.csv    {len(dt_anio):>8,} filas")
    print(f"    dim_producto.csv  {len(dp_anio):>8,} filas")
    print(f"    dim_vendedor.csv  {len(dv_anio):>8,} filas")
    print(f"    dim_cliente.csv   {len(dc_anio):>8,} filas")
    print(f"    dim_region.csv    {len(dim_region):>8,} filas")

print("\n" + "=" * 60)
print("DIVISION COMPLETADA")
print(f"Archivos en: {OUTPUT_DIR}")
print("=" * 60)
