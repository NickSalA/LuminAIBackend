# src/api/usuarios_api.py
import httpx
import oracledb
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import asyncio

# --- ¡NUEVAS IMPORTACIONES DE GOOGLE! ---
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# Importa tus utilidades
from src.db.session import get_connection
from src.core.security import (
    create_access_token, 
    get_current_user,
    GOOGLE_CLIENT_ID, 
    GOOGLE_CLIENT_SECRET, 
    GOOGLE_REDIRECT_URI
)

# Constantes (igual que antes)
AGE_URL = "https://people.googleapis.com/v1/people/me?personFields=birthdays"
NAME_EMAIL_URL = "https://www.googleapis.com/userinfo/v2/me"

routerUsuarios = APIRouter()

# --- Modelos Pydantic (igual que antes) ---
class GoogleAuthCode(BaseModel):
    code: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# --- Función auxiliar (igual que antes) ---
async def fetch_google_data(url: str, access_token: str, client: httpx.AsyncClient):
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    try:
        response = await client.get(url, headers=headers)
        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Access Token de Google expirado o inválido.")
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Error al obtener datos de Google: {e.response.json()}")

# --- Endpoint de Autenticación (¡LÓGICA MODIFICADA!) ---
@routerUsuarios.post("/auth/google", response_model=TokenResponse)
async def google_auth(
    auth_data: GoogleAuthCode, 
    db: oracledb.Connection = Depends(get_connection)
):
    
    # --- 1. Configurar el Flujo de OAuth (como el 'new google.auth.OAuth2') ---
    # Usamos la configuración de tu .env
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=[ # Los scopes que definimos antes
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/user.birthday.read"
        ],
        redirect_uri=GOOGLE_REDIRECT_URI
    )

    # --- 2. Canjear el Código por Tokens (como 'oauth2Client.getToken') ---
    try:
        # Esta función hace la llamada POST a https://oauth2.googleapis.com/token
        # usando el 'code', 'client_id', 'client_secret' y 'redirect_uri'
        flow.fetch_token(code=auth_data.code)
        
        access_token_google = flow.credentials.token
        if not access_token_google:
            raise HTTPException(status_code=400, detail="No se pudo obtener el Access Token de Google.")

    except Exception as e:
        # Si las credenciales en tu .env (ID o Secret) son incorrectas,
        # ¡fallará aquí con un error 401 (invalid_client)!
        print(f"Error detallado al canjear el código: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Fallo al canjear el código (invalid_client?): {str(e)}")

    # --- 3. Obtener datos del usuario (¡igual que antes!) ---
    try:
        async with httpx.AsyncClient() as client:
            personal_data_task = fetch_google_data(NAME_EMAIL_URL, access_token_google, client)
            age_data_task = fetch_google_data(AGE_URL, access_token_google, client)
            personal_data, age_data = await asyncio.gather(personal_data_task, age_data_task)

            p_email = personal_data.get('email')
            p_google_name = personal_data.get('name')
            p_google_id = personal_data.get('id')
            
            # (Procesar age_data si es necesario)

            if not p_email or not p_google_id:
                raise HTTPException(status_code=400, detail="Google no devolvió email o ID del usuario.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo datos de Google: {str(e)}")

    # --- 4. Llamar al Paquete de Oracle (¡igual que antes!) ---
    try:
        with db.cursor() as cursor:
            id_usuario_out = cursor.var(oracledb.NUMBER)
            
            cursor.callproc(
                "PKG_USER_REGISTRATION.HANDLE_GOOGLE_LOGIN",
                [p_email, p_google_name, p_google_id, id_usuario_out]
            )
            
            id_usuario_interno = id_usuario_out.getvalue()
            
            if not id_usuario_interno:
                raise Exception("El procedimiento de login no devolvió un ID de usuario.")
        
        db.commit()

    except oracledb.DatabaseError as e:
        db.rollback() 
        raise HTTPException(status_code=500, detail=f"Error en base de datos al procesar login: {str(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno (Oracle): {str(e)}")

    # --- 5. Creación de TU Token JWT (¡igual que antes!) ---
    access_token_propio = create_access_token(
        data={"sub": str(id_usuario_interno)} 
    )

    # --- 6. Respuesta al Frontend ---
    return TokenResponse(access_token=access_token_propio)

#TODO cambiar el uri del playground a la app cuando sea necesario 