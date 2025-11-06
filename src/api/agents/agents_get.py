# Rutas API para analistas
from fastapi import APIRouter, Request, HTTPException
from src.flow.flow_agente_tutor import FlowAgenteTutor
from src.flow.flow_preguntas import FlowAgentePreguntas
from src.flow.flow_respuestas import FlowAgenteRespuestas
from src.flow.flow_retroalimentacion import FlowAgenteRetroalimentacion

# Modelos
from pydantic import BaseModel

agents_get_router = APIRouter()

class ChatIn(BaseModel):
    mensaje: str

@agents_get_router.post("/tutor")
def obtener_tutor(req: Request, body: ChatIn):
    user =  {}#req.session.get("user")
    seccion = {} # req.session.get("seccion")
    # if not user: # PARA TESTEAR
    #     raise HTTPException(status_code=401, detail="Usuario no autenticado")

    # if not seccion: # PARA TESTEAR
    #     raise HTTPException(status_code=401, detail="Sección no especificada")
    saver = getattr(req.app.state, "checkpointer", None)
    if saver is None:
        raise HTTPException(500, "server_config: checkpointer ausente")
    
    orq = FlowAgenteTutor(user, seccion, saver=saver)
    if user.get("thread_id") != orq.user.get("thread_id"):
        user["thread_id"] = orq.user.get("thread_id")
        req.session["user"] = user
    try:
        respuesta = orq.responderMensaje(body.mensaje)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error al enviar el mensaje: {e}')
    return {"respuesta": respuesta}

@agents_get_router.post("/preguntas")
def obtener_preguntas(req: Request):
    seccion = {} # req.session.get("seccion")
    # if not seccion:  # PARA TESTEAR
    #     raise HTTPException(status_code=401, detail="Sección no especificada")

    orq = FlowAgentePreguntas(seccion)
    try:
        preguntas = orq.generarPreguntas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error al generar preguntas: {e}')
    return {"preguntas": preguntas}
    
@agents_get_router.post("/respuestas")
def obtener_respuestas(req: Request):
    seccion = {} # req.session.get("seccion")
    preguntas = {} # req.session.get("preguntas") -- NO SE SABE BIEN COMO OBTENER LAS PREGUNTAS 
    respuestas = {} # req.session.get("respuestas") -- NO SE SABE BIEN COMO OBTENER LAS RESPUESTAS
    # if not seccion: 
    #     raise HTTPException(status_code=401, detail="Sección no especificada")
    
    orq = FlowAgenteRespuestas(seccion, preguntas, respuestas)
    try:
        evaluacion = orq.evaluarRespuestas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error al evaluar respuestas: {e}')
    return {"evaluacion": evaluacion}

@agents_get_router.post("/retroalimentacion/bienvenida")
def obtener_retroalimentacion(req: Request):
    user =  {}#req.session.get("user")
    seccion = {} # req.session.get("seccion")
    preguntas = {} # req.session.get("preguntas") -- NO SE SABE BIEN COMO OBTENER LAS PREGUNTAS 
    respuestas = {} # req.session.get("respuestas") -- NO SE SABE BIEN COMO OBTENER LAS RESPUESTAS
    # if not user: # PARA TESTEAR
    #     raise HTTPException(status_code=401, detail="Usuario no autenticado")

    # if not seccion: # PARA TESTEAR
    #     raise HTTPException(status_code=401, detail="Sección no especificada")
    
    orq = FlowAgenteRetroalimentacion(user, seccion, preguntas, respuestas)
    try:
        retroalimentacion = orq.darRetroalimentacion()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error al generar retroalimentación: {e}')
    return {"retroalimentacion": retroalimentacion}

@agents_get_router.post("/retroalimentacion/mensaje")
def responder_retroalimentacion(req: Request, body: ChatIn):
    user =  {}#req.session.get("user")
    seccion = {} # req.session.get("seccion")
    preguntas = {} # req.session.get("preguntas") -- NO SE SABE BIEN COMO OBTENER LAS PREGUNTAS 
    respuestas = {} # req.session.get("respuestas") -- NO SE SABE BIEN COMO OBTENER LAS RESPUESTAS
    # if not user: # PARA TESTEAR
    #     raise HTTPException(status_code=401, detail="Usuario no autenticado")

    # if not seccion: # PARA TESTEAR
    #     raise HTTPException(status_code=401, detail="Sección no especificada")
    
    orq = FlowAgenteRetroalimentacion(user, seccion, preguntas, respuestas)
    try:
        respuesta = orq.responderMensaje(body.mensaje)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error al enviar el mensaje: {e}')
    return {"respuesta": respuesta}