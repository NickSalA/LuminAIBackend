from src.agents.agente_evaluador import AgenteEvaluador
from src.util.util_llm import obtenerModelo
from langchain_core.prompts import ChatPromptTemplate
from src.tools.tool_buscar_base_conocimientos import BC_Tool

def PromptEvaluador(seccion: dict, preguntas: dict = {}, respuestas: dict = {}):
    seccion = seccion or {}
    tema = seccion.get("tema", "Tema no especificado")
    nivel = seccion.get("nivel", "Nivel no especificado")
    lenguaje = seccion.get("lenguaje", "Python")

    informacionSeccion = f"""
INFORMACIÓN DE LA SECCIÓN:
- Tema: {tema}
- Lenguaje: {lenguaje, "Python"}
- Nivel: {nivel}
"""

    identidad = """
Eres 'EvaluadorAI', un asistente especializado en calificar respuestas de prácticas de programación.

Tu objetivo:
Analizar las respuestas del usuario basándote en las preguntas de la práctica y asignar una calificación por pregunta.

Criterios de calificación:
1. **Corrección técnica**: la respuesta es funcional y correcta en Python.
2. **Relevancia**: la respuesta aborda directamente la pregunta.
3. **Claridad y coherencia**: la respuesta está bien estructurada, comprensible y sigue una lógica clara.

Indicaciones:
- No des explicaciones largas ni retroalimentación.
- Solo califica.
- Usa valores de puntaje entre 0 y 1 (puede ser decimal si es parcialmente correcto).
- Evalúa cada pregunta de forma independiente.
"""

    formatoEvaluacion = """
FORMATO DE SALIDA (único y obligatorio):
{
  "resultados": [
    {
      "id": "<id_pregunta>",
      "puntaje": <0.0 a 1.0>
    }
  ],
  "puntaje_total": <suma total>,
  "puntaje_maximo": <numero_total_de_preguntas>
}

REGLAS:
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

    instrucciones = """
Analiza las respuestas del usuario según las preguntas y devuelve SOLO el JSON con los puntajes.
"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", informacionSeccion),
        ("system", identidad),
        ("system", formatoEvaluacion),
        ("system", contexto),
        ("system", instrucciones),
    ])

    return prompt
class FlowAgenteRespuestas:
    def __init__(self,seccion: dict, preguntas: dict = {}, respuestas: dict = {}):
        self.llm = obtenerModelo()
        self.AgenteEvaluador = AgenteEvaluador(
            llm=self.llm,
            contexto=PromptEvaluador(seccion, preguntas, respuestas),
            tools=[BC_Tool()],
        )
    def evaluarRespuesta(self, mensaje: str = ""):
        return self.AgenteEvaluador.responder(mensaje)