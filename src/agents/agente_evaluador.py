from langchain_google_genai import ChatGoogleGenerativeAI
from src.util.util_agente import crearAgenteSinMemoria, ejecutarSinMemoria

class AgenteEvaluador:
    def __init__(self,
        llm: ChatGoogleGenerativeAI,
        contexto: str,
        tools: list | None = None,
    ):
        self.llm = llm
        self.contexto = contexto
        self.tools = tools or []
        self.agente = crearAgenteSinMemoria(llm, contexto, self.tools)
    
    def responder(self, consulta: str = ""):
        return ejecutarSinMemoria(self.agente, consulta)
