# Rutas API para analistas
from fastapi import APIRouter, Request, HTTPException

# Modelos
from pydantic import BaseModel, ConfigDict
from datetime import datetime
import uuid

agents_get_router = APIRouter()

@agents_get_router.get("/chat")
def obtener_chat():
    return {"mensaje": "Este es el endpoint para obtener el chat"}