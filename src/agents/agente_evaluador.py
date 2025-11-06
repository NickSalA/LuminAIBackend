from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from src.util.util_agente import crearAgente, ejecutar

import uuid
from langgraph.checkpoint.memory import InMemorySaver

class AgenteEvaluador:
    def __init__(self,
        llm: ChatGoogleGenerativeAI,
        contexto: str,
        tools: list | None = None,
        memoria=None,
    ):
        self.llm = llm
        self.contexto = contexto
        self.tools = tools or []
        self.memoria = memoria
        self.agente = crearAgente(llm, contexto, self.tools, self.memoria)
    
    def responder(self, consulta: str = ""):
        return ejecutar(self.agente, consulta)
