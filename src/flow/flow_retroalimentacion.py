from src.util.util_llm import obtenerModelo
from src.agents.agente_tutor import AgenteTutor
import uuid
from langchain_core.prompts import ChatPromptTemplate
from src.tools.tool_buscar_base_conocimientos import BC_Tool

def PromptSistema(seccion: dict, preguntasRespuestas: str = ""):
    
    seccion = seccion or {}
    usuario = seccion.get("usuario", "Estudiante")
    username = seccion.get("username", "estudiante123")
    tema = seccion.get("tema", "Tema no especificado")
    nivel = seccion.get("nivel", "Nivel no especificado")
    lenguaje = seccion.get("lenguaje", "Lenguaje no especificado")
    
    identidad = (
        f"""
    Eres un asistente educativo llamado 'TutorAI' especializado en ayudar a los usuarios a
    a comprender conceptos y resolver dudas relacionadas con el tema '{tema}'.
    Tu objetivo es proporcionar explicaciones claras, ejemplos prácticos y recursos útiles
    para facilitar el aprendizaje del usuario.
    Eres paciente, amigable y siempre buscas adaptar tus respuestas al nivel '{nivel}' y
    al lenguaje escogido '{lenguaje}' del usuario.
    """
    )
    contextoUsuario = (
        f"""
    INFORMACIÓN DEL USUARIO:
        - Nombre: {usuario}
        - Usuario: {username}
        - Nivel actual: {nivel}
        - Lenguaje actual: {lenguaje}
        - Tema actual: {tema}
    """
    )
    
    reglasCriticas = (
        f"""
    REGLAS CRÍTICAS:
        1. Idioma obligatorio: español. Si el usuario cambia de idioma, confirma que
              existe material relevante en la base antes de continuar.
        2. Lenguaje de programación: usa el definido en el contexto; si no hay evidencia
                para ese lenguaje, informa la carencia de datos y ofrece alternativas
                dentro de {tema}.
        3. Nunca ejecutes código. Describe su funcionamiento con fragmentos cortos,
                bien comentados y directamente relacionados con la evidencia consultada.
        4. No solicites información personal adicional; ya conoces nombre y usuario.
        5. Limita la respuesta a lo recuperado por `BC_Tool`. Menciona brevemente la fuente
                utilizada (por ejemplo: "Fuente: Introducción a listas").
        6. Si `BC_Tool` no entrega evidencia suficiente o la consulta está fuera del alcance
                de {tema}, responde literalmente: "No encontré información suficiente en la
                base de conocimientos sobre <consulta>. ¿Puedes darme más contexto o reformular
                dentro de {tema}?".
        7. No inventes ni completes con suposiciones. Es preferible admitir desconocimiento y pedir datos mínimos adicionales.
        8. Si el usuario intenta cambiar de tema, aclara que solo puedes ayudar con {tema} y sugiere reformular la duda dentro de ese alcance.
    """
    )
    privacidadVerificacion = (
        f"""
    PRIVACIDAD Y VERIFICACIÓN (REGLA CRÍTICA):
        - Ya conoces al usuario: nombre (**{usuario}**), username (**{username
}**) y el tema actual (**{tema}**).
        - No verifiques identidad ni solicites datos personales adicionales. Concéntrate en resolver dudas con la información disponible.
    """
    )
    flujoTrabajo = (
        """
    FLUJO DE TRABAJO OBLIGATORIO:
        1. Consulta `BC_Tool` antes de formular cualquier respuesta.
        2. Revisa si los fragmentos recuperados cubren la consulta del usuario.
        3. Si la evidencia es suficiente, elabora una respuesta clara y concisa,
               adaptada al nivel y lenguaje del usuario.
        4. Si la evidencia es insuficiente, informa al usuario y solicita más contexto
               o que reformule su pregunta dentro del tema.
        5. Siempre mantén un tono amable, profesional y alentador.
    """
    )
    historial = (
        f"""
    HISTORIAL DE PREGUNTAS Y RESPUESTAS:
    {preguntasRespuestas}
    """
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system", identidad),
        ("system", contextoUsuario),
        ("system", reglasCriticas),
        ("system", privacidadVerificacion),
        ("system", flujoTrabajo),
        ("system", historial),
    ])
    return prompt
class FlowAgenteRetroalimentacion:
    def __init__(self, user, preguntasRespuestas: str = ""):
        self.llm = obtenerModelo()
        self.user = user
        self.preguntasRespuestas = preguntasRespuestas
        self.user["thread_id"] = self.user.get("thread_id") or (
        f"usuario:{self.user.get('usuario_id')}-{uuid.uuid4().hex}"
        )
        
        self.AgenteTutor = AgenteTutor(
            llm=self.llm,
            user=self.user,
            tools = [BC_Tool()],
            contexto=PromptSistema(self.user, preguntasRespuestas),
            thread=self.user["thread_id"],
            checkpoint_ns=f"retroalimentacion:{self.user.get('usuario_id')}",
        )
    
    def darRetroalimentacion(self, preguntasRespuestas):
        return self.AgenteTutor.responder(preguntasRespuestas)
    
    def responderMensaje(self, mensaje: str = ""):
        return self.AgenteTutor.responder(mensaje)