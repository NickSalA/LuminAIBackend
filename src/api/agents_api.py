# Rutas API para agentes

# Utilitario para FastAPI
from fastapi import APIRouter, HTTPException

# Importa los flujos de agentes
from src.flow.flow_tutor import FlowAgenteTutor
from src.flow.flow_preguntas_diarias import FlowAgentePreguntasDiarias
from src.flow.flow_preguntas_practica import FlowAgentePreguntas
from src.flow.flow_respuestas import FlowAgenteRespuestas
from src.flow.flow_retroalimentacion import FlowAgenteRetroalimentacion

# Importa los esquemas de datos para las respuestas
from src.util.util_schemas import QuestionResultsJson, AgentMessageJson

# Importa los esquemas específicos para las solicitudes
from src.util.util_schemas import ChatIn, respuestasRequest, chatTutorRequest, chatRetroalimentacionRequest, preguntasRequest, preguntasDiariasRequest

# Utilitarios para datos opcionales
from typing import Optional
import uuid

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

@routerAgente.post("/practice")
async def obtener_preguntas(req: preguntasRequest):
  seccion = req.contextData or {}

  orq = FlowAgentePreguntas(seccion)
  
  try:
    preguntas = await orq.generarPreguntas()
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Error al generar preguntas: {e}')
  
  return preguntas

@routerAgente.post("/dailyPractice")
async def obtener_preguntas_diarias(req: preguntasDiariasRequest):
  sections = req.contextData or []

  orq = FlowAgentePreguntasDiarias(sections)
  
  try:
    preguntas = await orq.generarPreguntas()
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Error al generar preguntas diarias: {e}')
  
  return preguntas

@routerAgente.post("/practiceResults", response_model= QuestionResultsJson)
async def obtener_respuestas(req: respuestasRequest):
  questions = req.questions
  answers = req.answers
  
  orq = FlowAgenteRespuestas(questions, answers)
  try:
    evaluacion = await orq.evaluarRespuestas()
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Error al evaluar respuestas: {e}')
  
  return QuestionResultsJson(**evaluacion)

@routerAgente.post("/dailyPracticeResults", response_model= QuestionResultsJson)
async def obtener_respuestas_diarias(req: respuestasRequest):
  questions = req.questions
  answers = req.answers
  
  orq = FlowAgenteRespuestas(questions, answers)
  try:
    evaluacion = await orq.evaluarRespuestas()
  except Exception as e:
    raise HTTPException(status_code=500, detail=f'Error al evaluar respuestas: {e}')
  
  return QuestionResultsJson(**evaluacion)

@routerAgente.post("/feedback", response_model = AgentMessageJson)
async def obtener_retroalimentacion(req: chatRetroalimentacionRequest, body: Optional[ChatIn] = None):
  user =  req.userData
  seccion = req.contextData
  questions = req.questions
  answers = req.answers

  orq = FlowAgenteRetroalimentacion(user, seccion, questions, answers)
  thread = body.thread_id if body else None
  
  if not thread:
    thread = orq.reiniciarMemoria()
    try:
      feedback = await orq.darRetroalimentacion(thread)
    except Exception as e:
      raise HTTPException(status_code=500, detail=f'Error al generar retroalimentación: {e}')
    
  else:
    mensaje = body.mensaje if body else ""
    try:
      feedback = await orq.responderMensaje(mensaje, thread)
    except Exception as e:
      raise HTTPException(status_code=500, detail=f'Error al enviar el mensaje: {e}')
    
  return AgentMessageJson(text=feedback, thread_id=thread)

@routerAgente.post("/reset", response_model= str)
def reiniciarMemoria() -> str:
  thread = f"usuario:{'anon'}-{uuid.uuid4().hex}"
  return thread