# src/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer # Para extraer el token del header
from jose import JWTError, jwt # Para crear y verificar JWTs
from passlib.context import CryptContext

# --- Configuración ---
# ¡ESTA CLAVE DEBE SER SECRETA Y MUY LARGA! Guárdala de forma segura (ej: en util_credenciales)
SECRET_KEY = "LuminProyect" # ¡CAMBIAR ESTO!
ALGORITHM = "HS256" # Algoritmo estándar para firmar
ACCESS_TOKEN_EXPIRE_MINUTES = 500 # Cuánto tiempo dura la sesión

# Esquema para que FastAPI sepa cómo buscar el token ("Bearer" token en el header Authorization)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token") # tokenUrl es dummy aquí

# --- Funciones ---

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Crea un nuevo token JWT."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire}) # Añade tiempo de expiración
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
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