# export_data.py
# Conecta al DW y exporta los datos limpios para el frontend
import pandas as pd
import mysql.connector
import json
from datetime import datetime

# 1. Conexión
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="exbox360",  # Tu contraseña
    database="abarrotes_dw"
)

# 2. Query optimizada para frontend
query = """
SELECT 
    dt.fecha, dt.dia_semana, dt.mes, dt.anio,
    ds.nombre AS sucursal, ds.zona,
    dp.categoria, dp.nombre AS producto,
    dc.tipo_cliente,
    fv.cantidad, fv.total_venta, fv.descuento, fv.margen
FROM fact_ventas fv
JOIN dim_tiempo dt ON fv.sk_tiempo = dt.sk_tiempo
JOIN dim_sucursal ds ON fv.sk_sucursal = ds.sk_sucursal
JOIN dim_producto dp ON fv.sk_producto = dp.sk_producto
JOIN dim_cliente dc ON fv.sk_cliente = dc.sk_cliente
"""

df = pd.read_sql(query, conn)
conn.close()

# 3. Limpiar tipos para JSON
df['fecha'] = df['fecha'].astype(str)
df['total_venta'] = df['total_venta'].astype(float)
df['margen'] = df['margen'].astype(float)
df['descuento'] = df['descuento'].astype(float)

# 4. Exportar
records = df.to_dict('records')

# RUTA CORREGIDA: dashboard/data/ventas.json
with open('dashboard/data/ventas.json', 'w', encoding='utf-8') as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

print(f"✅ {len(records)} registros exportados a dashboard/data/ventas.json")
print("📦 Listo para subir a GitHub + Vercel")