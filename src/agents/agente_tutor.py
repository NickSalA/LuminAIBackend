from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from src.util.util_agente import crearAgente, ejecutar

import uuid
from langgraph.checkpoint.memory import InMemorySaver

class AgenteTutor:
    def __init__(self,
        llm: ChatGoogleGenerativeAI,
        user: dict,
        contexto: ChatPromptTemplate,
        thread: str = "",
        checkpoint_ns: str = "soporte",
        tools: list | None = None,
        memoria=None,
    ):
        self.llm = llm
        self.contexto = contexto
        self.tools = tools or []
        self.thread = thread
        self.checkpoint_ns = checkpoint_ns
        self.user = user
        self.memoria = memoria
        self.agente = crearAgente(llm, contexto, self.tools, self.memoria)
    
    def responder(self, consulta: str = ""):
        return ejecutar(self.agente, consulta, config= {
            "user": self.user,
            "thread": self.thread,
            "checkpoint_ns": self.checkpoint_ns,
        })

    def reiniciarMemoria(self) -> str:
        """
        Si es InMemorySaver: reinstancia y reconstruye el agente.
        Si es PostgresSaver: abre un nuevo thread.
        """
        # Siempre generamos un nuevo thread id para garantizar que la conversación
        # previa no se siga mezclando (independiente del tipo de saver)
        thread = f"persona:{self.user.get('persona_id') or 'anon'}-{uuid.uuid4().hex}"

        if isinstance(self.memoria, InMemorySaver):
            # Reinicia la memoria en RAM y reconstruye el agente con un nuevo hilo
            self.memoria = InMemorySaver()
        else:
            # Para almacenes persistentes simplemente cambiamos el thread
            self.thread = thread

        return self.thread