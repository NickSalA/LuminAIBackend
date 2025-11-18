from src.agents.agente_evaluador import AgenteEvaluador
from src.util.util_llm import obtenerModelo
from src.tools.tool_buscar_base_conocimientos import BC_Tool

def PromptEvaluador(p: dict = {}, r: dict = {}) -> str:
    preguntas = p.get("questions")
    respuestas = r.get("answers")
        
    lenguaje = "Python"

    identidad = f"""
    Eres un asistente especializado en calificar respuestas. Tu objetivo es analizar las respuestas del usuario basándote en las preguntas de la práctica y asignar una calificación por pregunta. Calificar y utilizar únicamente código en {lenguaje} cuando sea necesario.
    """
    
    criteriosDeCalificacion = f"""
    Criterios de calificación:
    1. **Corrección técnica**: la respuesta es funcional y correcta en {lenguaje}.
    2. **Relevancia**: la respuesta aborda directamente la pregunta.
    3. **Claridad y coherencia**: la respuesta está bien estructurada, comprensible y sigue una lógica clara.

    Validación de formato (obligatoria antes de calificar):
    Considera los siguientes tipos de preguntas y sus formatos:
    - SingleSelection: verifica que la respuesta sea una de las opciones proporcionadas.
    - FreeResponse: verifica que la respuesta incluya las palabras clave obligatorias y siga la rúbrica dada.
    - FixTheCode: verifica que el código corregido funcione según lo esperado y pase las pruebas I/O indicadas.
    - CompleteTheCode: verifica que el código completado sea correcto y utilice uno de los tokens proporcionados.
    """

    formatoEvaluacion = r"""
    FORMATO DE SALIDA (único y obligatorio):
    {
    results: [
            questionResults: [boolean, ...],  // true si la respuesta es correcta, false si es incorrecta
            resultType: "APPROVED" | "DISAPPROVED" | "FULLYAPPROVED", // "APPROVED": al menos 60% correcto, "DISAPPROVED": menos de 60% correcto, "FULLYAPPROVED": 100% correcto
            score: int // Puntaje total entre 0 y 1 por pregunta (5 max)
        ]
    }
    """
    
    reglas = """
    REGLAS IMPORTANTES:
    - Devuelve solo JSON válido.
    - No incluyas explicaciones ni texto fuera del JSON.
    """
    
    # Construir contexto dinámico de preguntas y respuestas
    contexto = f"""
    PREGUNTAS Y RESPUESTAS A EVALUAR:
    Preguntas: {preguntas}
    Respuestas del usuario: {respuestas}
    """


    message = (
        identidad,
        criteriosDeCalificacion,
        formatoEvaluacion,
        reglas,
        contexto,
    )
    prompt = "\n".join(message)
    return prompt

class FlowAgenteRespuestas:
    def __init__(self,preguntas: dict = {}, respuestas: dict = {}):
        self.llm = obtenerModelo()
        self.AgenteEvaluador = AgenteEvaluador(
            llm=self.llm,
            contexto=PromptEvaluador(preguntas, respuestas),
            tools=[BC_Tool()],
        )
        
    async def evaluarRespuestas(self):
        return await self.AgenteEvaluador.responder("Evalúa las respuestas proporcionadas según las preguntas dadas y devuelve SOLO el JSON con los puntajes.")