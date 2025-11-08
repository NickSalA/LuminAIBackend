from src.agents.agente_evaluador import AgenteEvaluador
from src.util.util_llm import obtenerModelo
from src.tools.tool_buscar_base_conocimientos import BC_Tool

def PromptEvaluador(seccion: dict, p: dict = {}, r: dict = {}) -> str:
    preguntas = p.get("preguntas")
    respuestas = r.get("respuestas")
    
    tema = seccion.get("tema", "Introducción a If y Bucles")
    nivel = seccion.get("nivel", "Básico")
    
    lenguaje = "Python"
    
    informacionSeccion = f"""
    INFORMACIÓN DE LA SECCIÓN:
    - Tema: {tema}
    - Lenguaje: {lenguaje}
    - Nivel: {nivel}
    """

    identidad = f"""
    Eres un asistente especializado en calificar respuestas del tema "{tema}". Tu objetivo es analizar las respuestas del usuario basándote en las preguntas de la práctica y asignar una calificación por pregunta. Te debes adecuar al nivel "{nivel}" para calificar y utilizar únicamente código en {lenguaje} cuando sea necesario.
    """
    
    criteriosDeCalificacion = f"""
    Criterios de calificación:
    1. **Corrección técnica**: la respuesta es funcional y correcta en {lenguaje}.
    2. **Relevancia**: la respuesta aborda directamente la pregunta.
    3. **Claridad y coherencia**: la respuesta está bien estructurada, comprensible y sigue una lógica clara.

    Indicaciones:
    - No des explicaciones ni retroalimentación.
    - Solo califica.
    - Usa valores de puntaje entre 0 y 1.
    - Evalúa cada pregunta de forma independiente.
    """

    formatoEvaluacion = """
    FORMATO DE SALIDA (único y obligatorio):
    {
    "results": [
        {
        "id": "<id_pregunta>",
        "points": <0.0 o 1.0>
        }
    ],
    "total_points": <suma total>,
    "max_points": <numero_total_de_preguntas>
    }
    """
    
    reglas = """
    REGLAS IMPORTANTES:
    - Devuelve solo JSON válido.
    - No incluyas explicaciones ni texto fuera del JSON.
    - Usa los IDs de las preguntas recibidas.
    """
    
    # Construir contexto dinámico de preguntas y respuestas
    contexto = f"""
    PREGUNTAS Y RESPUESTAS A EVALUAR:
    Preguntas: {preguntas}
    Respuestas del usuario: {respuestas}
    """


    message = (
        informacionSeccion,
        identidad,
        criteriosDeCalificacion,
        formatoEvaluacion,
        reglas,
        contexto,
    )
    prompt = "\n".join(message)
    return prompt

class FlowAgenteRespuestas:
    def __init__(self,seccion: dict, preguntas: dict = {}, respuestas: dict = {}):
        self.llm = obtenerModelo()
        self.AgenteEvaluador = AgenteEvaluador(
            llm=self.llm,
            contexto=PromptEvaluador(seccion, preguntas, respuestas),
            tools=[BC_Tool()],
        )
        
    def evaluarRespuestas(self):
        return self.AgenteEvaluador.responder("Evalúa las respuestas proporcionadas según las preguntas dadas y devuelve SOLO el JSON con los puntajes.")