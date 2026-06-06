# analisis_fase5.py — Fase 5: Análisis y Minería para Abarrotes El Valle
# Requisitos: pip install pandas matplotlib seaborn scikit-learn mysql-connector-python

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import mysql.connector
import warnings
warnings.filterwarnings('ignore')

# Configurar estilo de gráficas
sns.set_style('whitegrid')
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 10

# ==========================================
# 1. CONEXIÓN AL DATA WAREHOUSE
# ==========================================
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='exbox360',
    database='abarrotes_dw'
)

print("🔍 Iniciando Análisis Fase 5...")

# ==========================================
# 2. ANÁLISIS EXPLORATORIO BÁSICO
# ==========================================

# --- 2.1 KPIs Generales ---
print("\n📈 Calculando KPIs...")
kpis = pd.read_sql("""
    SELECT 
        COUNT(DISTINCT sk_venta) AS total_transacciones,
        ROUND(SUM(total_venta), 2) AS ingresos_totales,
        ROUND(AVG(total_venta), 2) AS ticket_promedio,
        ROUND(SUM(margen), 2) AS margen_total,
        ROUND(AVG(margen)/AVG(total_venta)*100, 2) AS margen_porcentaje
    FROM fact_ventas
""", conn)

print(f"\n📊 KPIs del negocio:")
for col in kpis.columns:
    print(f"   • {col}: {kpis[col].values[0]:,}")

# --- 2.2 Ventas por Categoría ---
print("\n📦 Analizando ventas por categoría...")
df_categoria = pd.read_sql("""
    SELECT 
        dp.categoria,
        COUNT(*) AS unidades_vendidas,
        ROUND(SUM(fv.total_venta), 2) AS ingresos,
        ROUND(SUM(fv.margen), 2) AS margen_total,
        ROUND(AVG(fv.margen)/AVG(fv.total_venta)*100, 2) AS margen_pct
    FROM fact_ventas fv
    JOIN dim_producto dp ON fv.sk_producto = dp.sk_producto
    GROUP BY dp.categoria
    ORDER BY ingresos DESC
""", conn)

print(df_categoria.to_string(index=False))

# Gráfica: Ingresos vs Margen por categoría
plt.figure(figsize=(10, 5))
sns.barplot(data=df_categoria, x='categoria', y='ingresos', color='skyblue', label='Ingresos')
sns.barplot(data=df_categoria, x='categoria', y='margen_total', color='coral', label='Margen')
plt.title('💰 Ingresos vs Margen por Categoría', fontsize=14, fontweight='bold')
plt.xlabel('Categoría')
plt.ylabel('Monto ($)')
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig('categoria_ingresos_margen.png', dpi=300)
print("✅ Gráfica guardada: categoria_ingresos_margen.png")
plt.close()

# --- 2.3 Ventas por Sucursal ---
print("\n🏪 Analizando ventas por sucursal...")
df_sucursal = pd.read_sql("""
    SELECT 
        ds.nombre AS sucursal,
        ds.zona,
        COUNT(*) AS total_ventas,
        ROUND(SUM(fv.total_venta), 2) AS ingresos,
        ROUND(AVG(fv.margen), 2) AS margen_promedio
    FROM fact_ventas fv
    JOIN dim_sucursal ds ON fv.sk_sucursal = ds.sk_sucursal
    GROUP BY ds.sk_sucursal, ds.nombre, ds.zona
    ORDER BY ingresos DESC
""", conn)

print(df_sucursal.to_string(index=False))

# Gráfica: Ingresos por sucursal
plt.figure(figsize=(8, 5))
sns.barplot(data=df_sucursal, x='sucursal', y='ingresos', palette='viridis')
plt.title('🏪 Ingresos por Sucursal', fontsize=14, fontweight='bold')
plt.xlabel('Sucursal')
plt.ylabel('Ingresos Totales ($)')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('sucursales_ingresos.png', dpi=300)
print("✅ Gráfica guardada: sucursales_ingresos.png")
plt.close()

# --- 2.4 Estacionalidad: Heatmap por día/hora ---
print("\n🕐 Analizando patrones horarios...")
df_horario = pd.read_sql("""
    SELECT 
        dt.dia_semana,
        HOUR(v.fecha_hora) AS hora,
        COUNT(*) AS total_ventas
    FROM fact_ventas fv
    JOIN dim_tiempo dt ON fv.sk_tiempo = dt.sk_tiempo
    JOIN abarrotes.ventas v ON fv.sk_venta = (
        SELECT MIN(sk_venta) FROM fact_ventas WHERE sk_tiempo = fv.sk_tiempo LIMIT 1
    )
    GROUP BY dt.dia_semana, HOUR(v.fecha_hora)
    ORDER BY FIELD(dt.dia_semana, 'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'), hora
""", conn)

# Crear heatmap (simplificado para evitar JOIN complejo)
df_heatmap = pd.read_sql("""
    SELECT 
        dt.dia_semana,
        CASE 
            WHEN HOUR(v.fecha_hora) BETWEEN 8 AND 11 THEN 'Mañana (8-11)'
            WHEN HOUR(v.fecha_hora) BETWEEN 12 AND 15 THEN 'Mediodía (12-15)'
            WHEN HOUR(v.fecha_hora) BETWEEN 16 AND 19 THEN 'Tarde (16-19)'
            ELSE 'Noche (20-22)'
        END AS periodo,
        COUNT(*) AS ventas
    FROM fact_ventas fv
    JOIN dim_tiempo dt ON fv.sk_tiempo = dt.sk_tiempo
    JOIN abarrotes.ventas v ON fv.sk_venta = (
        SELECT sk_venta FROM fact_ventas WHERE sk_tiempo = fv.sk_tiempo LIMIT 1
    )
    GROUP BY dt.dia_semana, periodo
    ORDER BY FIELD(dt.dia_semana, 'Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday')
""", conn)

pivot_heatmap = df_heatmap.pivot(index='dia_semana', columns='periodo', values='ventas')

plt.figure(figsize=(10, 6))
sns.heatmap(pivot_heatmap, annot=True, fmt='.0f', cmap='YlOrRd', linewidths=0.5)
plt.title('🔥 Ventas por Día y Periodo del Día', fontsize=14, fontweight='bold')
plt.xlabel('Periodo')
plt.ylabel('Día de la Semana')
plt.tight_layout()
plt.savefig('heatmap_estacionalidad.png', dpi=300)
print("✅ Gráfica guardada: heatmap_estacionalidad.png")
plt.close()

# ==========================================
# 3. MINERÍA DE DATOS: K-MEANS PARA CLIENTES
# ==========================================
print("\n🤖 Aplicando K-Means para segmentar clientes...")

# Extraer características por cliente
df_clientes = pd.read_sql("""
    SELECT 
        dc.id_cliente_origen,
        dc.tipo_cliente,
        COUNT(fv.sk_venta) AS frecuencia_compra,
        ROUND(SUM(fv.total_venta), 2) AS gasto_total,
        ROUND(AVG(fv.total_venta), 2) AS ticket_promedio,
        ROUND(AVG(fv.margen), 2) AS margen_promedio
    FROM fact_ventas fv
    JOIN dim_cliente dc ON fv.sk_cliente = dc.sk_cliente
    GROUP BY dc.id_cliente_origen, dc.tipo_cliente
""", conn)

# Preparar datos para clustering (solo clientes registrados, excluir anónimos)
df_cluster = df_clientes[df_clientes['tipo_cliente'] != 'anonimo'].copy()

if len(df_cluster) > 0:
    # Variables para clustering
    X = df_cluster[['frecuencia_compra', 'gasto_total', 'ticket_promedio']].copy()
    
    # Estandarizar (K-Means es sensible a escalas)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Determinar número óptimo de clusters (método del codo)
    inertias = []
    k_range = range(2, 6)
    for k in k_range:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans.fit(X_scaled)
        inertias.append(kmeans.inertia_)
    
    # Gráfica del codo
    plt.figure(figsize=(8, 5))
    plt.plot(k_range, inertias, 'bo-', linewidth=2)
    plt.xlabel('Número de Clusters (K)')
    plt.ylabel('Inercia')
    plt.title('📐 Método del Codo para Seleccionar K')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('kmeans_elbow.png', dpi=300)
    print("✅ Gráfica guardada: kmeans_elbow.png")
    plt.close()
    
    # Aplicar K-Means con K=3 (típico: bajo/medio/alto valor)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df_cluster['cluster'] = kmeans.fit_predict(X_scaled)
    
    # Analizar características de cada cluster
    resumen_clusters = df_cluster.groupby('cluster').agg({
        'frecuencia_compra': 'mean',
        'gasto_total': 'mean',
        'ticket_promedio': 'mean',
        'id_cliente_origen': 'count'
    }).round(2).rename(columns={'id_cliente_origen': 'n_clientes'})
    
    print("\n📊 Resumen de Clusters:")
    print(resumen_clusters)
    
    # Visualizar clusters (2D con PCA simplificado: gasto vs frecuencia)
    plt.figure(figsize=(8, 6))
    scatter = plt.scatter(
        df_cluster['frecuencia_compra'], 
        df_cluster['gasto_total'],
        c=df_cluster['cluster'],
        cmap='viridis',
        s=50,
        alpha=0.7,
        edgecolors='black'
    )
    plt.xlabel('Frecuencia de Compra')
    plt.ylabel('Gasto Total ($)')
    plt.title('🎯 Segmentación de Clientes con K-Means (K=3)')
    plt.colorbar(scatter, label='Cluster')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('kmeans_segmentacion.png', dpi=300)
    print("✅ Gráfica guardada: kmeans_segmentacion.png")
    plt.close()
    
    # Guardar resultados para dashboard
    df_cluster.to_csv('segmentacion_clientes.csv', index=False)
    print("✅ Datos guardados: segmentacion_clientes.csv")
else:
    print("⚠️ No hay clientes registrados para clustering (solo anónimos)")

# ==========================================
# 4. CIERRE
# ==========================================
conn.close()

print("\n" + "="*60)
print("🎉 FASE 5 COMPLETADA: Análisis y Minería finalizados")
print("📁 Archivos generados:")
print("   • categoria_ingresos_margen.png")
print("   • sucursales_ingresos.png") 
print("   • heatmap_estacionalidad.png")
print("   • kmeans_elbow.png")
print("   • kmeans_segmentacion.png")
print("   • segmentacion_clientes.csv (si aplica)")
print("="*60)