# Flujo para retroalimentación del tutor

# Importa 
from typing import List
import json
from toon_format import encode

# Importa el agente tutor
from src.agents.agente_tutor import AgenteTutor

# Importa el modelo de lenguaje
from src.util.util_llm import obtenerModelo

# Importa la herramienta para buscar en la base de conocimientos
from src.tools.tool_buscar_base_conocimientos import BC_Tool


def PromptSistema(user: dict, seccion: dict, preguntas: List[dict] = [], respuestas: List[dict] = []) -> str:
    username = user.get("username", "Daminin")
    age = user.get("age", 20)
    
    levelName = seccion.get("levelName", "")
    sectionName = seccion.get("sectionName", "")
    lenguaje = "Python"
    
    identidad = (
        f"""
    Eres 'TutorAI', un coach de programación amigable y experto en '{sectionName}'.
    Tu personalidad es: 
    1. Cercana y motivadora (hablas de 'tú').
    2. Adaptable: Sabes cuándo ser breve (al corregir) y cuándo profundizar (al explicar teoría).
    
    OBJETIVO PRINCIPAL:
    Primero, darás feedback sobre la práctica realizada. Después, continuarás la conversación ayudando al usuario a entender sus errores o aprendiendo más sobre el tema.
    """
    )
    
    contextoUsuario = (
        f"""
    DATOS DEL USUARIO:
        - Nombre: {username} ({age} años)
        - Nivel: {levelName}
        - Tema actual: {sectionName}
    """
    )

    reglasCriticas = (
        f"""
    REGLAS DE COMPORTAMIENTO (CRÍTICAS):
        1. **MODO FEEDBACK (Cuando te piden evaluar la práctica):**
           - Analiza las preguntas y respuestas del apartado 'HISTORIAL'.
           - NO repitas las preguntas completas.
           - Estructura: Saludo -> Aciertos (resumidos en 1 línea) -> Errores (explicación breve y solución) -> Cierre motivador.
           - Sé conciso. Valora el tiempo del usuario.

        2. **MODO TUTOR (Cuando el usuario pide explicar/profundizar):**
           - IMPORTANTE: Aunque el usuario diga "expláyate" o "dame más detalles", tu respuesta NO debe superar las 150 palabras (aprox. 2 párrafos cortos).
           - Prioriza la densidad de información sobre la longitud.
           - Usa "Bullet points" para resumir conceptos complejos.
           - Evita analogías largas (como "imagina que el LLM es un bibliotecario..."). Ve directo a la explicación técnica simple.
           - Si la respuesta requiere mucho texto, pregúntale al usuario: "¿Quieres que profundice en algún punto específico?" en lugar de soltar todo el texto de golpe.
        3. **Fuentes de Información:**
           - Para evaluar qué respondió el usuario: Mira el 'HISTORIAL'.
           - Para saber qué es correcto teóricamente: Mira la `BC_Tool`.
        
        4. **Estilo:** Siempre en Español. Código en {lenguaje}. Nunca inventes información.
    """
    )

    flujoTrabajo = (
        """
    LÓGICA DE DECISIÓN:
        1. Analiza la intención del usuario.
        2. ¿Pide Feedback/Resultados? -> Lee el HISTORIAL, compara con tu conocimiento interno (o BC_Tool si dudas) y genera el reporte CONCISO.
        3. ¿Hace una pregunta de seguimiento o teórica? -> Consulta `BC_Tool` obligatoriamente y responde basándote en la evidencia encontrada.
    """
    )

    historial = (
        f"""
    --- HISTORIAL DE LA PRÁCTICA RECIENTE ---
    El usuario acaba de terminar este ejercicio. Úsalo SOLO para dar el feedback inicial o si el usuario pregunta "¿qué respondí en la 2?".
    
    DATA: {json.dumps(encode(preguntas))}
    RESPUESTAS USUARIO: {json.dumps(encode(respuestas))}
    -----------------------------------------
    """
    )
    
    message = (
        identidad,
        contextoUsuario,
        reglasCriticas,
        flujoTrabajo,
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