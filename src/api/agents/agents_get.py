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
    return respuesta

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
    return preguntas
    
@agents_get_router.post("/respuestas")
def obtener_respuestas(req: Request):
    seccion = {} # req.session.get("seccion")
    preguntas = {
  "preguntas": [
    {
      "id": "q1",
      "type": "unique_selection",
      "description": "¿Qué valor tendrá la variable 'resultado' después de ejecutar el siguiente código?",
      "initial_code": "x = 10\nif x > 5:\n    resultado = \"Mayor\"\nelse:\n    resultado = \"Menor o igual\"",
      "options": [
        "Mayor",
        "Menor o igual",
        "Error",
        "10"
      ]
    },
    {
      "id": "q2",
      "type": "free_answer",
      "description": "Explica brevemente qué es y para qué se utiliza un bucle 'for' en Python."
    },
    {
      "id": "q3",
      "type": "fix_code",
      "description": "El siguiente código intenta imprimir números del 1 al 5. Corrige los errores para que funcione correctamente.",
      "initial_code": "i = 0\nwhile i < 5:\nprint(i)\ni += 1"
    },
    {
      "id": "q4",
      "type": "complete_code",
      "description": "Completa el siguiente código para que imprima los números del 0 al 2.",
      "initial_code": "for i in _____:\n    print(i)",
      "options": [
        "range(3)",
        "range(0, 3)",
        "range(2)",
        "range(1, 3)"
      ]
    },
    {
      "id": "q5",
      "type": "unique_selection",
      "description": "¿Cuál de las siguientes afirmaciones sobre la cláusula 'else' en una estructura 'if-else' es verdadera?",
      "options": [
        "La cláusula 'else' siempre se ejecuta.",
        "La cláusula 'else' se ejecuta si la condición 'if' es verdadera.",
        "La cláusula 'else' se ejecuta si la condición 'if' es falsa.",
        "La cláusula 'else' es obligatoria en cada 'if'."
      ]
    }
  ]
} # req.session.get("preguntas") -- NO SE SABE BIEN COMO OBTENER LAS PREGUNTAS 
    respuestas = {
  "respuestas": [
    { "id": "q1", "option_index": 0 },
    { "id": "q2", "answer": "Un bucle 'for' en Python se utiliza para repetir un bloque de código un número determinado de veces, recorriendo elementos de una secuencia como listas, cadenas o rangos." },
    { "id": "q3", "code": "i = 0\nwhile i < 5:\n    print(i)\n    i += 1" },
    { "id": "q4", "option_indices": [1] },
    { "id": "q5", "option_index": 2 }
  ]
} # req.session.get("respuestas") -- NO SE SABE BIEN COMO OBTENER LAS RESPUESTAS
    # if not seccion: 
    #     raise HTTPException(status_code=401, detail="Sección no especificada")
    
    orq = FlowAgenteRespuestas(seccion, preguntas, respuestas)
    try:
        evaluacion = orq.evaluarRespuestas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error al evaluar respuestas: {e}')
    return evaluacion

@agents_get_router.post("/retroalimentacion/bienvenida")
def obtener_retroalimentacion(req: Request):
    user =  {}#req.session.get("user")
    seccion = {} # req.session.get("seccion")
    preguntas = {
  "preguntas": [
    {
      "id": "q1",
      "type": "unique_selection",
      "description": "¿Qué valor tendrá la variable 'resultado' después de ejecutar el siguiente código?",
      "initial_code": "x = 10\nif x > 5:\n    resultado = \"Mayor\"\nelse:\n    resultado = \"Menor o igual\"",
      "options": [
        "Mayor",
        "Menor o igual",
        "Error",
        "10"
      ]
    },
    {
      "id": "q2",
      "type": "free_answer",
      "description": "Explica brevemente qué es y para qué se utiliza un bucle 'for' en Python."
    },
    {
      "id": "q3",
      "type": "fix_code",
      "description": "El siguiente código intenta imprimir números del 1 al 5. Corrige los errores para que funcione correctamente.",
      "initial_code": "i = 0\nwhile i < 5:\nprint(i)\ni += 1"
    },
    {
      "id": "q4",
      "type": "complete_code",
      "description": "Completa el siguiente código para que imprima los números del 0 al 2.",
      "initial_code": "for i in _____:\n    print(i)",
      "options": [
        "range(3)",
        "range(0, 3)",
        "range(2)",
        "range(1, 3)"
      ]
    },
    {
      "id": "q5",
      "type": "unique_selection",
      "description": "¿Cuál de las siguientes afirmaciones sobre la cláusula 'else' en una estructura 'if-else' es verdadera?",
      "options": [
        "La cláusula 'else' siempre se ejecuta.",
        "La cláusula 'else' se ejecuta si la condición 'if' es verdadera.",
        "La cláusula 'else' se ejecuta si la condición 'if' es falsa.",
        "La cláusula 'else' es obligatoria en cada 'if'."
      ]
    }
  ]
} # req.session.get("preguntas") -- NO SE SABE BIEN COMO OBTENER LAS PREGUNTAS 
    respuestas = {
  "respuestas": [
    { "id": "q1", "option_index": 0 },
    { "id": "q2", "answer": "Un bucle 'for' en Python se utiliza para repetir un bloque de código un número determinado de veces, recorriendo elementos de una secuencia como listas, cadenas o rangos." },
    { "id": "q3", "code": "i = 0\nwhile i < 5:\n    print(i)\n    i += 1" },
    { "id": "q4", "option_indices": [1] },
    { "id": "q5", "option_index": 2 }
  ]
}
 # req.session.get("respuestas") -- NO SE SABE BIEN COMO OBTENER LAS RESPUESTAS
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