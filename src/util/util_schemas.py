# Esquemas de datos para utilitarios y agentes

# Utilitario para modelos de datos
from pydantic import BaseModel, Field

# Utilitarios para datos opcionales
from typing import List, Optional

# Modelos para recibir la información
class chatTutorRequest(BaseModel):
    contextData: dict = Field (default={"levelName": "string", "sectionName": "string"}, description="Datos de contexto adicionales para el agente.")
    userData: dict = Field (default={"username":"string", "age":"string"}, description="Datos del usuario para el agente.")

class chatRetroalimentacionRequest(BaseModel):
    contextData: dict = Field (default={"levelName": "string", "sectionName": "string"}, description="Datos de contexto adicionales para el agente.")
    userData: dict = Field (default={"username": "string", "age": "string"}, description="Datos del usuario para el agente.")
    questions: List[dict] = Field (default=[], description="Preguntas realizadas por el agente.")
    answers: List[dict] = Field (default=[], description="Respuestas proporcionadas por el usuario.")

class preguntasRequest(BaseModel):
    contextData: dict = Field (default={"levelName": "string","sectionName": "string"}, description="Datos de contexto adicionales para el agente.")
    
class respuestasRequest(BaseModel):
    questions: List[dict] = Field (default= [], description="Preguntas realizadas por el agente.")
    answers: List[dict] = Field (default= [], description="Respuestas proporcionadas por el usuario.")
    userData: dict = Field(default={"sectionId": 0}, description="Datos del usuario o contexto (ej: sectionId).")

# Modelos para las solicitudes de chat

class ChatIn(BaseModel):
    mensaje: str = Field (default="string", description="El mensaje del usuario al agente.")
    thread_id: Optional[str] = Field (default=None, description="El ID único de la conversación. Enviar 'null' o 'None' si es el primer mensaje.")

# Modelos para las respuestas del agente

class AgentMessageJson(BaseModel):
    text: str
    type: str = "AGENT"
    thread_id: str
    

# Modelo para las métricas que se devuelven al finalizar la calificación de una práctica

class CalificationJson(BaseModel):
    sectionId: int
    score: int
    retries: int
    passed: bool

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