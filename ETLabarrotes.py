#Leonardo Castrejon Angeles
#conexion con base de datos
import mysql.connector
# ==========================================
# 1. CONEXIONES
# ==========================================
conn_origen = mysql.connector.connect(
    host="localhost",
    user="root",
    password="exbox360",
    database="abarrotes"
)

conn_destino = mysql.connector.connect(
    host="localhost",
    user="root",
    password="exbox360",
    database="abarrotes_dw"
)

cursor_origen = conn_origen.cursor()
cursor_destino = conn_destino.cursor()

print("🚀 Iniciando ETL Básico...")

# ==========================================
# 2. CARGAR DIMENSIONES (INSERT INTO ... SELECT)
# ==========================================

# --- 2.1 Dimensión Tiempo ---
print("⏳ Cargando dim_tiempo...")
sql_tiempo = """
INSERT INTO dim_tiempo (fecha, dia, mes, anio, dia_semana, trimestre, es_fin_de_semana)
SELECT DISTINCT 
    DATE(fecha_hora) as fecha,
    DAY(fecha_hora) as dia,
    MONTH(fecha_hora) as mes,
    YEAR(fecha_hora) as anio,
    DAYNAME(fecha_hora) as dia_semana,
    QUARTER(fecha_hora) as trimestre,
    CASE WHEN DAYOFWEEK(fecha_hora) IN (1, 7) THEN 1 ELSE 0 END as es_fin_de_semana
FROM abarrotes.ventas
ORDER BY fecha
"""
cursor_destino.execute(sql_tiempo)
conn_destino.commit()
print(f"✅ {cursor_destino.rowcount} fechas cargadas")

# --- 2.2 Dimensión Producto ---
print("📦 Cargando dim_producto...")
sql_producto = """
INSERT INTO dim_producto (id_producto_origen, sku, nombre, categoria, es_perecedero)
SELECT id_producto, sku, nombre, categoria, es_perecedero
FROM abarrotes.productos
"""
cursor_destino.execute(sql_producto)
conn_destino.commit()
print(f"✅ {cursor_destino.rowcount} productos cargados")

# --- 2.3 Dimensión Sucursal ---
print("🏪 Cargando dim_sucursal...")
sql_sucursal = """
INSERT INTO dim_sucursal (id_sucursal_origen, nombre, zona, gerente, fecha_apertura)
SELECT id_sucursal, nombre, zona, 'Gerente Asignado', '2024-01-01'
FROM abarrotes.sucursales
"""
cursor_destino.execute(sql_sucursal)
conn_destino.commit()
print(f"✅ {cursor_destino.rowcount} sucursales cargadas")

# --- 2.4 Dimensión Cliente ---
print("👤 Cargando dim_cliente...")
sql_cliente = """
INSERT INTO dim_cliente (id_cliente_origen, tipo_cliente, colonia, antiguedad_dias)
SELECT id_cliente, tipo_cliente, colonia, 0
FROM abarrotes.clientes
"""
cursor_destino.execute(sql_cliente)
conn_destino.commit()
print(f"✅ {cursor_destino.rowcount} clientes cargados")

# ==========================================
# 3. CARGAR FACT_VENTAS (con JOINs y cálculos)
# ==========================================
print("📊 Cargando fact_ventas...")

sql_fact = """
INSERT INTO fact_ventas (
    sk_tiempo, sk_sucursal, sk_producto, sk_cliente,
    cantidad, subtotal, descuento, total_venta, costo_total, margen
)
SELECT 
    dt.sk_tiempo,
    ds.sk_sucursal,
    dp.sk_producto,
    dc.sk_cliente,
    dv.cantidad,
    dv.subtotal,
    v.descuento,
    v.total as total_venta,
    (dv.cantidad * p.costo) as costo_total,
    (v.total - (dv.cantidad * p.costo)) as margen
FROM abarrotes.ventas v
JOIN abarrotes.detalle_venta dv ON v.id_venta = dv.id_venta
JOIN abarrotes.productos p ON dv.id_producto = p.id_producto
JOIN dim_tiempo dt ON DATE(v.fecha_hora) = dt.fecha
JOIN dim_sucursal ds ON v.id_sucursal = ds.id_sucursal_origen
JOIN dim_producto dp ON dv.id_producto = dp.id_producto_origen
JOIN dim_cliente dc ON v.id_cliente = dc.id_cliente_origen
"""

cursor_destino.execute(sql_fact)
conn_destino.commit()
print(f"✅ {cursor_destino.rowcount} registros de ventas cargados")

# ==========================================
# 4. CIERRE
# ==========================================
cursor_origen.close()
cursor_destino.close()
conn_origen.close()
conn_destino.close()

print("\n🎉 FASE 4 COMPLETADA: ETL finalizado exitosamente")
print("📊 Tu Data Warehouse está listo para análisis")