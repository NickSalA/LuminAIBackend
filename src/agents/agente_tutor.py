# Agente tutor con memoria, personalizado por usuario

# Utilitario para el modelo de lenguaje
from langchain_google_genai import ChatGoogleGenerativeAI

# Utilitarios para crear y ejecutar agentes
from src.util.util_agente import crearAgente, ejecutar

# Manejo de UUID para identificar sesiones de usuario
import uuid

class AgenteTutor:
    def __init__(self,
        llm: ChatGoogleGenerativeAI,
        contexto: str,
        checkpoint_ns: str = "lumin-tutor",
        tools: list | None = None,
        memoria=None,
    ):
        self.llm = llm
        self.contexto = contexto
        self.tools = tools or []
        self.checkpoint_ns = checkpoint_ns
        self.memoria = memoria
        self.agente = crearAgente(llm, contexto, self.tools, self.memoria)
    
    async def responder(self, consulta: str = "", thread_id: str = ""):
        return await ejecutar(self.agente, consulta, config={
                "configurable": {
                    "thread_id": f"{thread_id}",
                    "checkpoint_ns": f"{self.checkpoint_ns}",
                }
            })

    def reiniciarMemoria(self) -> str:
        thread = f"usuario:{'anon'}-{uuid.uuid4().hex}"
        return thread