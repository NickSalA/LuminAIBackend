# Rutas API para analistas
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from src.flow.flow_agente_tutor import FlowAgenteTutor
from src.flow.flow_preguntas import FlowAgentePreguntas
from src.flow.flow_respuestas import FlowAgenteRespuestas
from src.flow.flow_retroalimentacion import FlowAgenteRetroalimentacion
from src.util.util_schemas import ChatIn, QuestionResultsJson, AgentMessageJson, chatTutorRequest, chatRetroalimentacionRequest


routerAgente = APIRouter()

@routerAgente.post("/tutor", response_model= AgentMessageJson)
def obtener_tutor(req:chatTutorRequest, body: ChatIn):
    user = req.userData or {}
    seccion = req.contextData or {}
    
    
    orq = FlowAgenteTutor(user, seccion)
    if body.get("thread_id") != orq.user.get("thread_id"):
        user["thread_id"] = orq.user.get("thread_id")
        req.session["user"] = user
    try:
        respuesta = orq.responderMensaje(body.mensaje)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error al enviar el mensaje: {e}')
    return respuesta

@routerAgente.post("/preguntas")
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
    
@routerAgente.post("/respuestas")
def obtener_respuestas(req: Request):
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
    
    orq = FlowAgenteRespuestas(preguntas, respuestas)
    try:
        evaluacion = orq.evaluarRespuestas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error al evaluar respuestas: {e}')
    return evaluacion

@routerAgente.post("/retroalimentacion/bienvenida")
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

@routerAgente.post("/retroalimentacion/mensaje")
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