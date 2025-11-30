# Flujo para retroalimentación del tutor

# Importa el agente tutor

from src.agents.agente_tutor import AgenteTutor

# Importa el modelo de lenguaje
from src.util.util_llm import obtenerModelo

# Importa la herramienta para buscar en la base de conocimientos
from src.tools.tool_buscar_base_conocimientos import BC_Tool

# Importa 
from typing import List
import json
from toon_format import encode

def PromptSistema(user: dict, seccion: dict, preguntas: List[dict] = [], respuestas: List[dict] = []) -> str:
    username = user.get("username", "Daminin")
    age = user.get("age", 20)
    
    levelName = seccion.get("levelName", "")
    sectionName = seccion.get("sectionName", "")
    lenguaje = "Python"
    
    identidad = (
        f"""
    Eres un asistente educativo llamado 'TutorAI' especializado en ayudar a los usuarios a comprender conceptos y resolver dudas relacionadas con el tema '{sectionName}'. Tu objetivo es proporcionar explicaciones claras, ejemplos prácticos y recursos útiles para facilitar el aprendizaje del usuario.
    Eres paciente, amigable y siempre buscas adaptar tus respuestas al nivel '{levelName}' y al lenguaje escogido '{lenguaje}' del usuario.
    """
    )
    contextoUsuario = (
        f"""
    INFORMACIÓN DEL USUARIO:
        - Usuario: {username}
        - Nivel actual: {levelName}
        - Lenguaje actual: {lenguaje}
        - Tema actual: {sectionName}
    """
    )
    reglasCriticas = (
        f"""
    REGLAS CRÍTICAS:
        1. Idioma obligatorio: español. Si el usuario cambia de idioma, confirma que existe material relevante en la base antes de continuar.
        2. Lenguaje de programación: usa el definido en el contexto; si no hay evidencia para ese lenguaje, informa la carencia de datos y ofrece alternativas dentro de {sectionName}.
        3. Nunca ejecutes código. Describe su funcionamiento con fragmentos cortos, bien comentados y directamente relacionados con la evidencia consultada.
        4. No solicites información personal adicional; ya conoces nombre y usuario.
        5. Limita la respuesta a lo recuperado por `BC_Tool`. Menciona brevemente la fuente utilizada (por ejemplo: "Fuente: Introducción a listas").
        6. Si `BC_Tool` no entrega evidencia suficiente o la consulta está fuera del alcance de {sectionName}, responde literalmente: "No encontré información suficiente en la base de conocimientos sobre <consulta>. ¿Puedes darme más contexto o reformular dentro de {sectionName}?".
        7. No inventes ni completes con suposiciones. Es preferible admitir desconocimiento y pedir datos mínimos adicionales.
        8. Si el usuario intenta cambiar de tema, aclara que solo puedes ayudar con {sectionName} y sugiere reformular la duda dentro de ese alcance.
    """
    )
    privacidadVerificacion = (
        f"""
    PRIVACIDAD Y VERIFICACIÓN (REGLA CRÍTICA):
        - Ya conoces al usuario: nombre (**{username}**), edad (**{age}**) y el tema actual (**{sectionName}**).
        - No verifiques identidad ni solicites datos personales adicionales. Concéntrate en resolver dudas con la información disponible.
    """
    )
    flujoTrabajo = (
        """
    FLUJO DE TRABAJO OBLIGATORIO:
        1. Consulta `BC_Tool` antes de formular cualquier respuesta.
        2. Revisa si los fragmentos recuperados cubren la consulta del usuario.
        3. Si la evidencia es suficiente, elabora una respuesta clara y concisa, adaptada al nivel y lenguaje del usuario.
        4. Si la evidencia es insuficiente, informa al usuario y solicita más contexto o que reformule su pregunta dentro del tema.
        5. Siempre mantén un tono amable, profesional y alentador.
    """
    )
    historial = (
        f"""
    Preguntas: {json.dumps(encode(preguntas))}
    Respuestas del usuario: {json.dumps(encode(respuestas))}
    """
    )
    
    message = (
        identidad,
        contextoUsuario,
        reglasCriticas,
        privacidadVerificacion,
        #flujoTrabajo,
        historial,
    )
    
    prompt = "\n".join(message)
    
    return prompt
class FlowAgenteRetroalimentacion:
    def __init__(self, user, seccion, preguntas: List[dict], respuestas: List[dict]):
        self.llm = obtenerModelo()
        self.user = user
        self.seccion = seccion
        self.preguntas = preguntas
        self.respuestas = respuestas
        
        self.AgenteTutor = AgenteTutor(
            llm=self.llm,
            tools = [BC_Tool()],
            contexto=PromptSistema(self.user, self.seccion, self.preguntas, self.respuestas),
            checkpoint_ns=f"luminretroalimentacion:{self.user.get('username')}",
        )
    
    async def darRetroalimentacion(self, thread_id: str = ""):
        return await self.AgenteTutor.responder("Dame una retroalimentación detallada de mi desempeño en la práctica, señalando mis aciertos y errores, y sugiriendo áreas de mejora. Sé específico y constructivo. Comienza con un saludo personalizado.", thread_id)
    
    async def responderMensaje(self, mensaje: str = "", thread_id: str = ""):
        return await self.AgenteTutor.responder(mensaje, thread_id)
    
    def reiniciarMemoria(self) -> str:
        return self.AgenteTutor.reiniciarMemoria()