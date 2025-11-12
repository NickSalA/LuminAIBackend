# src/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer # Para extraer el token del header
from jose import JWTError, jwt # Para crear y verificar JWTs
from passlib.context import CryptContext
from dotenv import load_dotenv
import os


load_dotenv()  # Carga las variables de entorno desde el archivo .env
# --- Configuración ---
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 500 # El tiempo que dura tu sesión (ej: 8 horas)

# --- 2. Configuración de GOOGLE (para que la use tu API de login) ---
# Lee las credenciales de Google que pusiste en tu .env
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

# --- Validación de que todo cargó bien ---
if not SECRET_KEY:
    raise Exception("Error: JWT_SECRET_KEY no encontrada en .env. Inventa una clave larga y ponla ahí.")
if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET or not GOOGLE_REDIRECT_URI:
    raise Exception("Error: Faltan credenciales de Google (CLIENT_ID, CLIENT_SECRET o REDIRECT_URI) en .env.")

# Esquema para que FastAPI sepa cómo buscar el token ("Bearer" token en el header Authorization)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # tokenUrl es dummy aquí

# --- Funciones ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None): #data contiene la info que queremos guardar en el token
    """Crea un nuevo token JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire}) # Añade tiempo de expiración
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)): #el depends indica que FastAPI debe extraer el token usando el esquema definido arriba
    """
    Dependencia para verificar el token JWT y obtener el ID de usuario.
    FastAPI ejecutará esto *antes* de tu función de ruta.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Decodifica el token usando la clave secreta
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Extrae el ID de usuario (o lo que hayas guardado) del token
        user_id_str: str | None = payload.get("sub") # Usamos "sub" (subject) por convención
        if user_id_str is None:
            raise credentials_exception
            
        # Convierte el ID a entero (o tu tipo de dato)
        try:
            user_id = int(user_id_str)
        except ValueError:
             raise credentials_exception
             
        # (Opcional pero recomendado) Podrías buscar al usuario en la BD aquí
        # user = session.get(Usuario, user_id)
        # if user is None:
        #     raise credentials_exception
            
        # Devuelve el ID del usuario autenticado
        return {"user_id": user_id} 

    except JWTError:
        raise credentials_exception