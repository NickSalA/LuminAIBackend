from src.schemas.models import *
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class GoogleAuth(BaseModel):
    token : str

@router.post("auth/google") # porque los datos van en el body no en los params asi no se filtra info

async def google_auth(auth: GoogleAuth):
    
    # Aquí iría la lógica para autenticar con Google usando el token proporcionado
    if auth.token == "token_valido":
        return {"mensaje": "Autenticación exitosa"}
    else:
        raise HTTPException(status_code=401, detail="Token inválido")

