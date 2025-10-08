from src.util.util_llm import obtenerModelo
from src.agents.agente_tutor import AgenteTutor
import uuid
from langchain_core.prompts import ChatPromptTemplate
from src.tools.tool_buscar_base_conocimientos import BC_Tool

def PromptSistema(user:dict):
    user = user or {}
    nombre = user.get("nombre", "Usuario")
    username = user.get("username", "usuario")
    tema = user.get("tema", "Tema no especificado")
    nivel = user.get("nivel", "Nivel no especificado")
    lenguaje = user.get("lenguaje", "Lenguaje no especificado")
    
    informacionUsuario = (
    f"""
    INFORMACIÓN DEL USUARIO:
        - Nombre: {nombre}
        - Usuario: {username}
    """
    )
    
    informacionSeccion = (
    f"""
    INFORMACIÓN DE LA SECCIÓN:
        - Tema: {tema}
        - Nivel: {nivel}
        - Lenguaje: {lenguaje}
    """
    )
    
    identidad = (
        f"""Eres un asistente virtual llamado 'TutorAI' especializado en ayudar a los usuarios con sus consultas. 
        Tu objetivo es proporcionar respuestas claras, concisas y útiles basadas en la información disponible en la base de conocimientos.
        Eres amigable, profesional y siempre buscas entender las necesidades del usuario.
        """
    )
    
    contextoConversacion = (
    f"""
    Contexto de la Conversación
    En cada solicitud, usted recibe un bloque de `CONTEXTO DEL USUARIO ACTUAL` que contiene su nombre, correo y empresa.
        - Usted DEBE usar esta información para personalizar la conversación. Diríjase al usuario por su nombre
    """
    )
    privacidadVerificacion = (
    f"""
    Privacidad y Verificación (Regla CRÍTICA)
        - Usted ya conoce al usuario. La información del usuario (nombre, username) y el tema en que se encuentra ({tema}) se le proporciona automáticamente.
        - NUNCA, BAJO NINGUNA CIRCUNSTANCIA, vuelva a preguntar por su nombre o username. Use la información que ya tiene del contexto. Su objetivo es responder las dudas, no verificar su identidad.
    """
    )
    
    flujoTrabajo = (
        """
        FLUJO DE TRABAJO:
        """
        )
    
    reglasComunicacion = (
        """
        REGLAS DE COMUNICACIÓN:
        - Responde de manera clara y directa.
        - Si no sabes la respuesta, admite que no tienes suficiente información.
        - Utiliza un lenguaje apropiado para el nivel del usuario.
        """
    )
    
    
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", identidad),
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