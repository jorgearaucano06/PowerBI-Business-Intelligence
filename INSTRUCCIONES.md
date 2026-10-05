# Proyecto 3: Power BI + Azure SQL - Business Intelligence

## Objetivo
Crear un dashboard profesional en Power BI conectado a Azure SQL Database.
Cubre brechas de Power BI y Azure que piden empresas como YOFC.

## Tecnologias a usar
- **Power BI Desktop**: Desarrollo de reportes (gratis)
- **Power BI Service**: Publicacion online
- **Azure SQL Database**: Base de datos en la nube
- **DAX**: Medidas calculadas y KPIs
- **Power Query (M)**: Transformacion de datos
- **Azure Data Factory** (opcional): ETL hacia Azure SQL

## Problema de negocio
Una empresa de retail/distribucion necesita visibilidad en tiempo real
de sus operaciones: ventas por region, margenes por producto, tendencias
mensuales y deteccion de productos de bajo rendimiento. Hoy los reportes
se hacen en Excel manualmente, con demora de dias y sin interactividad.

**Pregunta de negocio:** Como crear un sistema de reporteria ejecutiva
que permita al gerente tomar decisiones en minutos, no en dias?

## Valor para el negocio
- Reduccion del tiempo de generacion de reportes (de dias a segundos)
- Deteccion temprana de caidas en ventas por region/producto
- Visibilidad de margenes para optimizar mix de productos
- Comparativas YoY/MoM automaticas para medir crecimiento

## Escala de datos
| Concepto | Valor |
|----------|-------|
| Dataset completo | 2-5 millones de transacciones de venta (3-5 anios historicos) |
| Muestra para demo | 200,000 - 500,000 registros (Azure SQL Free Tier: 32GB) |
| Fuentes publicas | Kaggle: Brazilian E-Commerce (100K+), Superstore (50K+), Instacart (3M+) |
| Nota de escalabilidad | Power BI soporta Direct Query para datasets grandes. Azure SQL escala verticalmente sin cambio en dashboards |

## Datos sugeridos
Opciones:
1. **Brazilian E-Commerce (Kaggle)**: 100K+ pedidos reales de Olist (2016-2018)
2. **Instacart Market Basket (Kaggle)**: 3+ millones de pedidos de grocery
3. Datos del MEF transformados para BI
4. Dataset sintetico de retail con multiples regiones/productos

## Fases de desarrollo
1. Crear cuenta Azure (Free Tier: $200 credito por 30 dias)
2. Crear Azure SQL Database y cargar datos
3. Instalar Power BI Desktop
4. Conectar Power BI a Azure SQL
5. Modelado dimensional: tablas de hechos y dimensiones (star schema)
6. Crear medidas DAX: YTD, MoM, YoY, margins, rankings
7. Pagina 1: Resumen Ejecutivo (KPIs principales)
8. Pagina 2: Analisis de Ventas (drill-down por region/producto)
9. Pagina 3: Analisis de Tendencias (series temporales)
10. Pagina 4: Detalle operativo (tabla con filtros)
11. Publicar en Power BI Service
12. README con screenshots de cada pagina

## Habilidades DAX a demostrar
- CALCULATE, FILTER, ALL, ALLEXCEPT
- Time intelligence: TOTALYTD, SAMEPERIODLASTYEAR, DATEADD
- Rankings: RANKX
- Conditional formatting
- Bookmarks y drill-through

## Resultado esperado
Dashboard publicado que demuestre dominio de Power BI + Azure,
con modelado dimensional, DAX avanzado y visualizaciones ejecutivas.

## Contexto del portafolio
Proyecto 3 de 7. El desarrollador ya tiene dashboards en Streamlit
pero necesita evidenciar Power BI y Azure.
