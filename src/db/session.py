# src/db/session.py
import oracledb
import os
from dotenv import load_dotenv
from fastapi import HTTPException

# 1. Carga las variables del archivo .env
load_dotenv()

# --- Configuración de Oracle (leída desde .env) ---
wallet_path = os.getenv("ORACLE_WALLET_PATH")
db_user = os.getenv("ORACLE_USER")
db_password = os.getenv("ORACLE_PASSWORD")
tns_name = os.getenv("ORACLE_TNS_NAME")
wallet_password = os.getenv("ORACLE_WALLET_PASSWORD")

pool = None # Inicia el pool como None

# Valida que las variables se cargaron antes de crear el pool
if not all([wallet_path, db_user, db_password, tns_name, wallet_password]):
    print("ERROR: Faltan variables de entorno de Oracle. Revisa tu archivo .env.")
else:
    print("Variables de entorno cargadas. Creando pool de conexiones de Oracle...")
    
    # --- 2. Crear el Pool de Conexiones (¡Esto es lo que querías!) ---
    try:
        pool = oracledb.create_pool(
            user=db_user,
            password=db_password,
            dsn=tns_name,
            config_dir=wallet_path,
            wallet_location=wallet_path,
            wallet_password=wallet_password,
            min=2, # Conexiones mínimas listas
            max=5, # Conexiones máximas
            increment=1 # Cuántas crear si se necesitan más
        )
        print("Pool de conexiones nativo de Oracle creado exitosamente.")
    except Exception as e:
        print(f"Error fatal al crear el pool de conexiones: {e}")

# --- 3. Dependencia de FastAPI (para tus APIs) ---
def get_connection():
    """
    Dependencia de FastAPI para "prestar" una conexión del pool.
    """
    if not pool:
        raise HTTPException(status_code=503, detail="Pool de conexiones no disponible.")
        
    connection = None
    try:
        # Pide una conexión prestada al pool
        connection = pool.acquire() 
        yield connection # Entrega la conexión a la API
    finally:
        # Cuando la API termina, devuelve la conexión al pool
        if connection:
            pool.release(connection) 

# --- 4. Función de Prueba (para ti) ---
def probar_conexion():
    """Intenta adquirir una conexión del pool para probar."""
    if not pool:
        print("No se puede probar la conexión, el pool no fue inicializado.")
        return False
        
    try:
        # Pide una conexión prestada, la usa, y la devuelve automáticamente
        with pool.acquire() as connection:
            print("¡Conexión de prueba (nativa) exitosa!")
            print(f"Versión de BD de Oracle: {connection.version}")
            return True
    except Exception as e:
        print(f"Hubo un error al probar la conexión del pool: {e}")
        return False

# --- Ejecutar la prueba ---
# Corre 'python src/db/session.py' en tu terminal para probar
if __name__ == "__main__":
    probar_conexion()