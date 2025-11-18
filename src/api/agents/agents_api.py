# Rutas API para analistas
from typing import Optional
from fastapi import APIRouter, Request, HTTPException
from src.flow.flow_agente_tutor import FlowAgenteTutor
from src.flow.flow_preguntas import FlowAgentePreguntas
from src.flow.flow_respuestas import FlowAgenteRespuestas
from src.flow.flow_retroalimentacion import FlowAgenteRetroalimentacion
from src.util.util_schemas import ChatIn, QuestionResultsJson, AgentMessageJson
from src.util.util_schemas import respuestasRequest, chatTutorRequest, chatRetroalimentacionRequest, preguntasRequest

routerAgente = APIRouter()

@routerAgente.post("/tutor", response_model= AgentMessageJson)
async def obtener_tutor(req:chatTutorRequest, body: ChatIn):
    user = req.userData or {}
    seccion = req.contextData or {}
    
    orq = FlowAgenteTutor(user, seccion)
    
    thread = body.thread_id
    if not thread:
      thread = orq.reiniciarMemoria()
    
    try:
        respuesta = await orq.responderMensaje(body.mensaje, thread)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error al enviar el mensaje: {e}')
    return AgentMessageJson(text=respuesta, thread_id=thread)

@routerAgente.post("/preguntas")
async def obtener_preguntas(req: preguntasRequest):
    seccion = req.contextData or {}

    orq = FlowAgentePreguntas(seccion)
    try:
        preguntas = await orq.generarPreguntas()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Error al generar preguntas: {e}')
    return preguntas
    
@routerAgente.post("/respuestas", response_model= QuestionResultsJson)
async def obtener_respuestas(req: respuestasRequest):
  questions = req.questions or {
  "questions": [
    {
      "id": "1",
      "type": "SINGLESELECTION",
      "description": "Selecciona la opción correcta sobre la sintaxis de los objetos JSON.",
      "question": "¿Qué carácter se utiliza para separar los pares clave-valor dentro de un objeto JSON?",
      "options": [
        "Punto y coma (;)",
        "Punto (.)",
        "Coma (,)",
        "Dos puntos (:)"
      ]
    },
    {
      "id": "2",
      "type": "FREERESPONSE",
      "description": "Explica la función principal de los corchetes en la sintaxis JSON.\nCriterios de evaluación:\n• Palabras clave obligatorias: 'colección ordenada', 'elementos', 'índice'.\n• Elementos a evitar: Confundir con objetos o diccionarios.\n• Rúbrica breve: 1. Menciona colección ordenada. 2. Menciona que contiene elementos. 3. Sugiere acceso por índice.",
      "question": "¿Para qué se utilizan los corchetes `[]` en la sintaxis JSON?"
    },
    {
      "id": "3",
      "type": "FIXTHECODE",
      "description": "El siguiente código Python intenta definir un string JSON válido, pero contiene un error de sintaxis. Corrige el 'wrongCode' para que el string 'json_data' sea un objeto JSON bien formado.\nComportamiento esperado: El string 'json_data' debe representar un objeto JSON válido.",
      "wrongCode": "json_data = '{\"nombre\": \"Luisa\", \"edad\": 28 \"ciudad\": \"Sevilla\"}'"
    },
    {
      "id": "4",
      "type": "COMPLETETHECODE",
      "description": "Completa el código Python para construir un objeto JSON que represente la información de un producto, y luego conviértelo a un string JSON. Asegúrate de que el precio sea un número y el nombre una cadena de texto.",
      "codeLines": [
        {
          "tokens": [
            {
              "token": "import"
            },
            {
              "token": "json"
            }
          ]
        },
        {
          "tokens": [
            {
              "token": " "
            }
          ]
        },
        {
          "tokens": [
            {
              "token": "producto"
            },
            {
              "token": "="
            },
            {
              "token": "{"
            }
          ]
        },
        {
          "tokens": [
            {
              "token": "INDENT"
            },
            {
              "token": "\"nombre\""
            },
            {
              "token": ":"
            },
            {
              "token": "MISSING"
            },
            {
              "token": "\"Laptop\""
            },
            {
              "token": ","
            }
          ]
        },
        {
          "tokens": [
            {
              "token": "\"precio\""
            },
            {
              "token": ":"
            },
            {
              "token": "MISSING"
            }
          ]
        },
        {
          "tokens": [
            {
              "token": "}"
            }
          ]
        },
        {
          "tokens": [
            {
              "token": " "
            }
          ]
        },
        {
          "tokens": [
            {
              "token": "json_string"
            },
            {
              "token": "="
            },
            {
              "token": "json.MISSING"
            },
            {
              "token": "("
            },
            {
              "token": "producto"
            },
            {
              "token": ","
            },
            {
              "token": "indent"
            },
            {
              "token": "="
            },
            {
              "token": "2"
            },
            {
              "token": ")"
            }
          ]
        }
      ],
      "missingTokens": [
        "\"",
        "1200.50",
        "dumps",
        "loads"
      ]
    },
    {
      "id": "5",
      "type": "SINGLESELECTION",
      "description": "Selecciona la opción correcta sobre la sintaxis de las claves en objetos JSON.",
      "question": "¿Cómo deben estar escritas las claves de un objeto JSON?",
      "options": [
        "Sin comillas, si son alfanuméricas",
        "Siempre entre comillas dobles",
        "Entre comillas simples o dobles",
        "Entre comillas dobles o sin comillas"
      ]
    }
  ]
}
  answers = req.answers or {
  
  } 
  orq = FlowAgenteRespuestas(questions, answers)
  try:
    evaluacion = await orq.evaluarRespuestas()
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