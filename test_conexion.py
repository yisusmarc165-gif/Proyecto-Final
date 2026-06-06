# test_conexion.py
import mysql.connector
from mysql.connector import Error

# ==========================================
# CONFIGURACIÓN - EDITA ESTO CON TUS DATOS
# ==========================================
DB_CONFIG = {
    'host': 'localhost',        # O '127.0.0.1'
    'user': 'root',             # Tu usuario de MariaDB
    'password': 'exbox360',             # Tu contraseña (deja vacío si no tiene)
    'database': 'abarrotes',    # La base que ya creaste
    'port': 3306                # Puerto por defecto de MariaDB
}

def probar_conexion():
    """Intenta conectar y hacer consultas básicas de verificación"""
    conn = None
    try:
        print("🔄 Intentando conectar a MariaDB...")
        conn = mysql.connector.connect(**DB_CONFIG)
        
        if conn.is_connected():
            print("✅ ¡Conexión exitosa!")
            
            # 1. Mostrar información del servidor
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"📦 Versión de MariaDB: {version[0]}")
            
            # 2. Verificar que la base de datos 'abarrotes' está seleccionada
            cursor.execute("SELECT DATABASE()")
            db_actual = cursor.fetchone()
            print(f"🗄️  Base de datos activa: {db_actual[0]}")
            
            # 3. Listar tablas existentes
            cursor.execute("SHOW TABLES")
            tablas = cursor.fetchall()
            print(f"\n📋 Tablas encontradas en 'abarrotes':")
            if tablas:
                for i, tabla in enumerate(tablas, 1):
                    print(f"   {i}. {tabla[0]}")
            else:
                print("   ⚠️  No hay tablas aún (¿ejecutaste el script SQL de creación?)")
            
            # 4. Prueba rápida: contar registros en una tabla existente
            if tablas:
                primera_tabla = tablas[0][0]
                cursor.execute(f"SELECT COUNT(*) FROM {primera_tabla}")
                cuenta = cursor.fetchone()
                print(f"\n🔍 Registros en '{primera_tabla}': {cuenta[0]}")
            
            cursor.close()
            return True
            
    except Error as e:
        print(f"❌ Error de conexión: {e}")
        print("\n💡 Posibles causas:")
        print("   • Usuario o contraseña incorrectos")
        print("   • MariaDB no está corriendo (revisa XAMPP/WAMP)")
        print("   • Puerto 3306 bloqueado por firewall")
        print("   • La base 'abarrotes' no existe")
        return False
        
    finally:
        if conn and conn.is_connected():
            conn.close()
            print("\n🔌 Conexión cerrada correctamente.")

# ==========================================
# EJECUCIÓN
# ==========================================
if __name__ == "__main__":
    exito = probar_conexion()
    if exito:
        print("\n🎉 ¡Todo listo para ejecutar tu script de generación de datos!")
    else:
        print("\n⚠️  Resuelve los errores de conexión antes de continuar.")