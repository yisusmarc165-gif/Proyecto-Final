# generar_datos_fase2.py
# Fase 2: Base de datos transaccional + Datos ficticios con Faker
# Proyecto: Abarrotes El Valle - Toluca, México

import mysql.connector
from faker import Faker
import random
from datetime import datetime, timedelta

# ==========================================
# 1. CONFIGURACIÓN DE CONEXIÓN
# ==========================================
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'exbox360',  # ← Tu contraseña real
    'database': 'abarrotes',
    'port': 3306
}

fake = Faker('es_MX')  # Datos realistas para México
random.seed(42)  # Para reproducibilidad en pruebas (opcional)

def get_conn():
    """Establece conexión con MariaDB"""
    return mysql.connector.connect(**DB_CONFIG)

# ==========================================
# 2. POBLAR CATÁLOGOS BASE
# ==========================================
def insertar_catalogos(conn):
    """Inserta datos maestros: sucursales, clientes, productos, empleados"""
    cursor = conn.cursor()
    
    # Limpiar datos previos para permitir re-ejecución segura
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
    cursor.execute("TRUNCATE detalle_venta")
    cursor.execute("TRUNCATE ventas")
    cursor.execute("TRUNCATE empleados")
    cursor.execute("TRUNCATE productos")
    cursor.execute("TRUNCATE clientes")
    cursor.execute("TRUNCATE sucursales")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
    print("🧹 Tablas limpiadas para nueva carga...")

    # --------------------------------------
    # 2.1 Sucursales (3 ubicaciones en Toluca)
    # --------------------------------------
    sucursales = [
        ('Matriz Centro', 'Av. Juárez 123, Centro', 'centro', '7221234567', '2020-01-15'),
        ('Sucursal San Mateo', 'Blvd. Isidro Fabela 456', 'san_mateo', '7229876543', '2021-03-10'),
        ('Sucursal San Antonio', 'Calle Morelos 789', 'san_antonio', '7225551234', '2022-06-20')
    ]
    cursor.executemany(
        "INSERT INTO sucursales (nombre, direccion, zona, telefono, fecha_apertura) VALUES (%s, %s, %s, %s, %s)",
        sucursales
    )
    print("✅ 3 sucursales insertadas")

    # --------------------------------------
    # 2.2 Clientes (1 anónimo + 50 ficticios)
    # CORRECCIÓN: 7 valores, sin None inicial (id es AUTO_INCREMENT)
    # --------------------------------------
    clientes = [
        ('Cliente General', None, None, None, 'anonimo', '2024-01-01', True)  # ID=1 reservado
    ]
    for _ in range(50):
        clientes.append((
            fake.name(), 
            fake.phone_number(), 
            fake.email(), 
            fake.city(), 
            random.choice(['regular','frecuente','mayoreo']), 
            fake.date_this_year(), 
            True
        ))
    cursor.executemany(
        "INSERT INTO clientes (nombre, telefono, email, colonia, tipo_cliente, fecha_registro, activo) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        clientes
    )
    print("✅ 51 clientes insertados (1 anónimo + 50 ficticios)")

    # --------------------------------------
    # 2.3 Productos (~60 items con precios realistas)
    # CORRECCIÓN: f-string cerrado con comilla simple, no backtick
    # --------------------------------------
    categorias = ['abarrotes','bebidas','limpieza','perecederos','otros']
    productos = [
        ('ARB-001','Arroz Grano de Oro 1kg','abarrotes',15.50,22.00,'kg',False,'2024-01-01'),
        ('BEB-001','Coca-Cola 600ml','bebidas',12.00,18.00,'pieza',False,'2024-01-01'),
        ('LIM-001','Fabuloso 1L','limpieza',18.00,28.00,'litro',False,'2024-01-01'),
        ('PER-001','Leche Lala 1L','perecederos',22.00,32.00,'litro',True,'2024-01-01'),
        ('OTR-001','Pilas AAA 4pk','otros',45.00,65.00,'paquete',False,'2024-01-01')
    ]
    # Generación automática del resto
    for i in range(2, 61):
        cat = random.choice(categorias)
        precio = round(random.uniform(10, 150), 2)
        productos.append((
            f'{cat[:3].upper()}-{i:03d}', 
            f'{fake.word().capitalize()} {random.choice(["Premium","Económico","Familiar","Industrial"])}',  # ✅ CORREGIDO
            cat, 
            round(precio*0.65, 2),  # costo = 65% del precio de venta
            precio, 
            'pieza', 
            cat=='perecederos',  # True solo si es categoría perecederos
            '2024-01-01'
        ))
    cursor.executemany(
        "INSERT INTO productos (sku, nombre, categoria, costo, precio_venta, unidad_medida, es_perecedero, fecha_alta) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        productos
    )
    print("✅ 60 productos insertados")

    # --------------------------------------
    # 2.4 Empleados (12 repartidos en las 3 sucursales)
    # --------------------------------------
    empleados = []
    for suc_id in [1,2,3]:
        for _ in range(4):
            empleados.append((
                fake.name(), 
                suc_id, 
                random.choice(['cajero','encargado_inventario','gerente','repartidor']),
                fake.date_this_year(), 
                round(random.uniform(8000, 15000), 2),
                f"{random.randint(7,9)}:00", 
                f"{random.randint(15,20)}:00", 
                True
            ))
    cursor.executemany(
        "INSERT INTO empleados (nombre_completo, id_sucursal, puesto, fecha_ingreso, sueldo_base, horario_entrada, horario_salida, activo) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        empleados
    )
    print("✅ 12 empleados insertados")
    
    conn.commit()
    print("🎯 Catálogos poblados correctamente.\n")

# ==========================================
# 3. GENERAR VENTAS Y DETALLES (6 MESES SIMULADOS)
# ==========================================
def generar_ventas(conn, num_ventas=8000):
    """Genera transacciones realistas con vinculación robusta venta-detalle"""
    cursor = conn.cursor()
    
    # Obtener IDs válidos para foreign keys
    cursor.execute("SELECT id_sucursal FROM sucursales")
    suc_ids = [r[0] for r in cursor.fetchall()]
    
    cursor.execute("SELECT id_cliente FROM clientes")
    cli_ids = [r[0] for r in cursor.fetchall()]
    
    cursor.execute("SELECT id_empleado FROM empleados")
    emp_ids = [r[0] for r in cursor.fetchall()]
    
    cursor.execute("SELECT id_producto, precio_venta FROM productos")
    prods = cursor.fetchall()  # Lista de tuplas: (id_producto, precio_venta)
    
    # Rango de fechas: últimos 180 días (6 meses)
    hoy = datetime.now()
    inicio = hoy - timedelta(days=180)
    
    # Estructura para vinculación robusta: cada venta guarda sus detalles
    ventas_para_insertar = []  # Lista de tuplas para INSERT en ventas
    detalles_para_insertar = []  # Lista de tuplas para INSERT en detalle_venta
    
    print(f"🔄 Generando {num_ventas} ventas simuladas...")
    
    for _ in range(num_ventas):
        # --- Fecha con patrón realista ---
        dias_offset = random.randint(0, 179)
        fecha_base = inicio + timedelta(days=dias_offset)
        # Pesos para simular picos de tráfico (más ventas 12pm-6pm y fines de semana)
        hora = random.choices(range(8, 22), weights=[1,1,2,3,4,4,3,2,3,4,4,3,2,1])[0]
        fecha_hora = fecha_base.replace(
            hour=hora, 
            minute=random.randint(0,59), 
            second=random.randint(0,59)
        )
        
        # --- Datos de la transacción ---
        suc_id = random.choice(suc_ids)
        emp_id = random.choice(emp_ids)
        # 85% ventas anónimas (id_cliente=1), 15% clientes registrados
        cli_id = 1 if random.random() < 0.85 else random.choice(cli_ids[1:])
        metodo = random.choices(['efectivo','tarjeta','movil'], weights=[0.6, 0.25, 0.15])[0]
        folio = f"V-{fecha_hora.strftime('%Y%m%d')}-{random.randint(1000,9999)}"
        
        # --- Generar líneas de detalle (1 a 5 productos por venta) ---
        num_items = random.randint(1, 5)
        items_seleccionados = random.sample(prods, num_items)
        subtotal_venta = 0
        
        detalles_de_esta_venta = []  # Guardamos los detalles temporalmente
        for prod_id, precio in items_seleccionados:
            cantidad = random.randint(1, 4)
            subtotal_item = float(precio)
            subtotal_venta += subtotal_item
            detalles_de_esta_venta.append((prod_id, cantidad, precio, subtotal_item))        
        # Descuento aleatorio (10% de las ventas tienen 5% de descuento)
        descuento = round(subtotal_venta * 0.05, 2) if random.random() < 0.10 else 0
        total = round(subtotal_venta - descuento, 2)
        
        # Guardar venta y sus detalles para inserción posterior
        ventas_para_insertar.append((
            folio, suc_id, emp_id, cli_id, fecha_hora, 
            subtotal_venta, descuento, total, metodo
        ))
        detalles_para_insertar.append(detalles_de_esta_venta)
    
    # --- Inserción masiva de cabeceras de venta ---
    cursor.executemany(
        "INSERT INTO ventas (folio, id_sucursal, id_empleado, id_cliente, fecha_hora, subtotal, descuento, total, metodo_pago) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        ventas_para_insertar
    )
    
    # --- Vinculación robusta: obtener IDs generados en orden secuencial ---
    # lastrowid da el primer ID generado; los siguientes son consecutivos
    primer_id_venta = cursor.lastrowid
    ids_ventas_generados = [primer_id_venta + i for i in range(num_ventas)]
    
    # --- Insertar detalles vinculados correctamente ---
    detalles_finales = []
    for idx_venta, detalles in enumerate(detalles_para_insertar):
        id_venta_actual = ids_ventas_generados[idx_venta]
        for prod_id, cantidad, precio, subtotal in detalles:
            detalles_finales.append((id_venta_actual, prod_id, cantidad, precio, subtotal))
    
    cursor.executemany(
        "INSERT INTO detalle_venta (id_venta, id_producto, cantidad, precio_unitario, subtotal) VALUES (%s, %s, %s, %s, %s)",
        detalles_finales
    )
    
    conn.commit()
    print(f"✅ {num_ventas} ventas y {len(detalles_finales)} líneas de detalle generadas exitosamente.")

# ==========================================
# 4. EJECUCIÓN PRINCIPAL
# ==========================================
if __name__ == "__main__":
    print("🚀 Iniciando carga de datos - Fase 2: Abarrotes El Valle\n")
    
    conn = None
    try:
        conn = get_conn()
        print("🔌 Conexión a MariaDB establecida\n")
        
        # Paso 1: Poblar catálogos
        insertar_catalogos(conn)
        
        # Paso 2: Generar transacciones
        generar_ventas(conn, num_ventas=8000)
        
        # Paso 3: Verificación rápida
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ventas")
        total_ventas = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM detalle_venta")
        total_detalles = cursor.fetchone()[0]
        cursor.execute("SELECT MIN(fecha_hora), MAX(fecha_hora) FROM ventas")
        rango = cursor.fetchone()
        
        print(f"\n📊 Verificación final:")
        print(f"   • Total ventas: {total_ventas:,}")
        print(f"   • Total líneas de detalle: {total_detalles:,}")
        print(f"   • Rango de fechas: {rango[0].date()} → {rango[1].date()}")
        print(f"\n🎉 Fase 2 COMPLETADA. Base lista para ETL y Data Warehouse.")
        
    except mysql.connector.Error as e:
        print(f"\n❌ Error de base de datos: {e}")
        print("💡 Verifica: contraseña, servicio MariaDB corriendo, nombre de base de datos")
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
    finally:
        if conn and conn.is_connected():
            conn.close()
            print("\n🔌 Conexión cerrada correctamente.")