from src.util.util_llm import obtenerModelo
from src.agents.agente_tutor import AgenteTutor
import uuid
from langchain_core.prompts import ChatPromptTemplate
from src.tools.tool_buscar_base_conocimientos import BC_Tool
def PromptSistema(user:dict):
    
    prompt = ChatPromptTemplate.from_messages([
        ("system","hola"),
    ])

    return prompt

class FlowAgenteTutor:
    def __init__(self, user, saver):
        self.llm = obtenerModelo()
        self.user = user
        self.saver = saver
        
        def obtenerSesion():
            return self.user

        def obtenerSaver():
            return self.saver

        self.user["thread_id"] = self.user.get("thread_id") or (
        f"persona:{self.user.get('persona_id')}-{uuid.uuid4().hex}"
        ) # CAMBIAR RESPECTO A LA BASE DE DATOS
        self.AgenteTutor = AgenteTutor(
            llm=self.llm,
            user=self.user,
            tools = [BC_Tool()],
            contexto=PromptSistema(self.user),
            thread=self.user["thread_id"],
            checkpoint_ns=f"cliente:{self.user.get('cliente_id')}", # CAMBIAR RESPECTO A LA BASE DE DATOS
        )
    def responderMensaje(self, mensaje: str = ""):
        return self.AgenteTutor.responder(mensaje)