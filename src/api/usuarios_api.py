from src.schemas.models import *
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.db.session import get_session
from sqlmodel import Session, select
from src.core.security import create_access_token, get_current_user

routerUsuarios = APIRouter()

class GoogleAuth(BaseModel):
    token : str

@routerUsuarios.post("/auth/google") # porque los datos van en el body no en los params asi no se filtra info

async def google_auth(auth: GoogleAuth):
    
    # Aquí iría la lógica para autenticar con Google usando el token proporcionado
    if auth.token == "token_valido":
        return {"mensaje": "Autenticación exitosa"}
    else:
        raise HTTPException(status_code=401, detail="Token inválido")

routerUsuarios.get("/lastpage", response_model=CuentaDeUsuarioBase)
# 1. La sesión se inyecta aquí, en los argumentos de la función
async def get_last_page( db: Session = Depends(get_session), current_user : dict = Depends(get_current_user)): 
    
    user_id = current_user.get("user_id")
    
    # 2. Construye el statement (¡perfecto!)
    statement = select(CuentaDeUsuario).where(CuentaDeUsuario.id_usuario == user_id) 
    
    # 3. Ejecuta y obtén el resultado (corrección de 'firts' a 'first')
    cuenta_usuario = db.exec(statement).scalars().first() 
    
    # 4. Verifica si se encontró el registro
    if not cuenta_usuario:
        raise HTTPException(status_code=404, detail="Cuenta de usuario no encontrada")
    
    # 5. Devuelve el objeto encontrado
    #    FastAPI usará CuentaDeUsuarioBase para filtrar los campos
    return cuenta_usuario #filtra solo los campos necesarios para CuentaDeUsuarioBase
