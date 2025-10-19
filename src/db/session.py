# src/db/session.py
from sqlmodel import create_engine, Session, SQLModel
import oracledb # Keep this import if needed for setup
import os

# --- Configuration (Your existing code) ---
wallet_path = "C:/Users/Fabrizio Mantari/OneDrive - Universidad Nacional Mayor de San Marcos/Escritorio/Recursos Varios/Wallet_lumin"
db_user = "ADMIN"
db_password = "Lumin_db_2025" # Consider getting this from util_credenciales instead of hardcoding
tns_name = "lumin_tp"

# Using f-string correctly for the URL
DATABASE_URL = f"oracle+oracledb://{db_user}:{db_password}@{tns_name}"

# --- Create Engine (Only once when the app starts) ---
engine = create_engine(DATABASE_URL, connect_args={
    "config_dir": wallet_path,
    "wallet_location": wallet_path,
    "wallet_password": "Lumin_db_2025" # Also consider getting this securely
}, echo=True) # echo=True is helpful for debugging SQL

# --- Session Generator (For FastAPI Dependency Injection) ---
def get_session():
    """
    Dependency function to get a database session per request.
    Handles opening and closing the session automatically.
    """
    with Session(engine) as session:
        yield session

# --- Connection Test Function (Keep it here for easy testing) ---
def probar_conexion():
    """Attempts to connect to the database using the engine."""
    try:
        # engine.connect() tries to establish a connection
        with engine.connect() as connection:
            print("¡Conexión exitosa a la base de datos Oracle!")
            return True
    except Exception as e:
        print("Hubo un error al conectar a la base de datos Oracle:")
        print(f"Detalle: {e}")
        return False

# --- Optional: Run connection test if script is executed directly ---
if __name__ == "__main__":
    probar_conexion()