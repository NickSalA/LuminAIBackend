# Rutas API para analistas
from fastapi import APIRouter, Request, HTTPException
from src.flow.flow_agente_tutor import FlowAgenteTutor

# Modelos
from pydantic import BaseModel

agents_get_router = APIRouter()

class ChatIn(BaseModel):
    mensaje: str

@agents_get_router.post("/tutor")
def obtener_tutor(req: Request, body: ChatIn):
    user =  {}#req.session.get("user")
    seccion = {} # req.session.get("seccion")
    if not user: # PARA TESTEAR
        user = {}
        # raise HTTPException(status_code=401, detail="Usuario no autenticado")

    if not seccion: # PARA TESTEAR
        seccion = {}
        # raise HTTPException(status_code=401, detail="Sección no especificada")

    orq = FlowAgenteTutor(user, seccion)
    if user.get("thread_id") != orq.user.get("thread_id"):
        user["thread_id"] = orq.user.get("thread_id")
        req.session["user"] = user
    try:
        respuesta = orq.responderMensaje(body.mensaje)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error al enviar el mensaje: {e}')
    return {"respuesta": respuesta}
