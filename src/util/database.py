from sqlmodel import create_engine, Session, SQLModel  
import oracledb
import os


wallet_path = "C:/Users/Fabrizio Mantari/OneDrive - Universidad Nacional Mayor de San Marcos/Escritorio/Recursos Varios/Wallet_lumin"

db_user = "ADMIN"
db_password = "Lumin_db_2025"
tns_name = "lumin_tp"

DATABASE_URL = f"oracle+oracledb://{db_user}:{db_password}@{tns_name}"

engine = create_engine(DATABASE_URL, connect_args = {
    "config_dir": wallet_path,
    "wallet_location": wallet_path,
    "wallet_password": "Lumin_db_2025"
}, echo=True)

def probar_conexion():
    try:
        conexion = engine.connect()
        print("conexion exitosa")
        return True
    except Exception as e:
        print("Hubo un error al conectar a la base de datos: ") 
        print(f"Detalle: {e}")
        return False
    
if __name__ == "__main__":
    probar_conexion()