"""
Explorar la estructura del dataset Brazilian E-Commerce de Olist.
Identifica problemas de calidad de datos antes de transformar.
"""
import pandas as pd
import os

RAW_DIR = r"C:\PROYECTOS\PowerBI-Business-Intelligence\data\raw"

archivos = [
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_products_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_sellers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "product_category_name_translation.csv",
]

for archivo in archivos:
    path = os.path.join(RAW_DIR, archivo)
    df = pd.read_csv(path)
    print(f"\n{'='*60}")
    print(f"ARCHIVO: {archivo}")
    print(f"Filas: {len(df):,}  |  Columnas: {len(df.columns)}")
    print(f"Columnas: {list(df.columns)}")
    print(f"\nNulos por columna:")
    nulos = df.isnull().sum()
    nulos_pct = (nulos / len(df) * 100).round(1)
    for col in df.columns:
        if nulos[col] > 0:
            print(f"  {col}: {nulos[col]:,} ({nulos_pct[col]}%)")
    if nulos.sum() == 0:
        print("  (sin nulos)")
    print(f"\nTipos de datos:")
    for col in df.columns:
        print(f"  {col}: {df[col].dtype}")
    print(f"\nPrimeras 3 filas:")
    print(df.head(3).to_string())
