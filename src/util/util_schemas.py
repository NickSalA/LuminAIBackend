# Esquemas de datos para utilitarios y agentes

# Utilitario para modelos de datos
from pydantic import BaseModel, Field

# Utilitarios para datos opcionales
from typing import List, Optional, Dict, Any

# Modelos para recibir la información
class chatTutorRequest(BaseModel):
    contextData: dict = Field (..., description="Datos de contexto adicionales para el agente.")
    userData: dict = Field (..., description="Datos del usuario para el agente.")

class chatRetroalimentacionRequest(BaseModel):
    contextData: dict = Field (..., description="Datos de contexto adicionales para el agente.")
    userData: dict = Field (..., description="Datos del usuario para el agente.")
    questions: dict = Field (..., description="Preguntas realizadas por el agente.")
    answers: dict = Field (..., description="Respuestas proporcionadas por el usuario.")

class preguntasRequest(BaseModel):
    contextData: dict = Field (default={
        "levelName": "",
        "sectionName": "",
        }, description="Datos de contexto adicionales para el agente.")

class preguntasDiariasRequest(BaseModel):
    contextData: list[str] = Field (..., description="Lista de temas para generar preguntas diarias.")
    
class respuestasRequest(BaseModel):
    questions: List[dict] = Field (..., description="Preguntas realizadas por el agente.")
    answers: List[dict] = Field (..., description="Respuestas proporcionadas por el usuario.")
    userData: Optional[Dict[str, Any]] = Field(default={"sectionId": int}, description="Datos del usuario o contexto (ej: sectionId).")

# Modelos para las solicitudes de chat

class ChatIn(BaseModel):
    mensaje: str = Field (..., description="El mensaje del usuario al agente.")
    thread_id: Optional[str] = Field (default=None, description="El ID único de la conversación. Enviar 'null' o 'None' si es el primer mensaje.")

# Modelos para las respuestas del agente

class AgentMessageJson(BaseModel):
    text: str = Field (..., description="La respuesta generada por el agente.")
    type: str = "AGENT"
    thread_id: str = Field (..., description="El ID único de la conversación.")
    
class QuestionResultsJson(BaseModel):
    questionsResults: list[bool] = Field (..., description="Lista de resultados por pregunta.")
    resultType: str = Field (..., description="Tipo de resultado: APPROVED, DISAPPROVED, FULLYAPPROVED.")
    score: int = Field (..., description="Puntaje total obtenido.")

class CalificationJson(BaseModel):
    sectionId: int
    score: int
    retries: int
    passed: bool

# Modelo para las métricas que se devuelven al finalizar
class UserMetrics(BaseModel):
    currentLevelId: int | None
    succededSectionsCount: int | None
    currentSectionId: int | None
    currentPageId: int | None
    averageScore: float | None
    totalPracticeRetries: int | None
    succededDailyPracticeCount: int | None
    totalSectionsCount: int | None

# Respuesta completa para /practiceResults
class PracticeResultsResponse(BaseModel):
    questionsResults: list[bool]
    resultType: str
    score: int
    userMetrics: UserMetrics
    calification: CalificationJson

# Respuesta completa para /dailyPracticeResults
class DailyPracticeResultsResponse(BaseModel):
    questionsResults: list[bool]
    resultType: str
    score: int
    succededDailyPracticeCount: int