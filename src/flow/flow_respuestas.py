# Flujo para evaluar respuestas de práctica

# Importa el agente evaluador
from src.agents.agente_evaluador import AgenteEvaluador

# Importa el modelo de lenguaje
from src.util.util_llm import obtenerModelo

# Importa la herramienta para buscar en la base de conocimientos
from src.tools.tool_buscar_base_conocimientos import BC_Tool

# Tipos
from typing import List
import json
from toon_format import encode

def PromptEvaluador(preguntas: List[dict], respuestas: List[dict] = []) -> str:
    lenguaje = "Python"

    identidad = f"""
    Eres un asistente especializado en calificar respuestas. Tu objetivo es analizar las respuestas del usuario basándote en las preguntas de la práctica y asignar una calificación por pregunta. Calificar y utilizar únicamente código en {lenguaje} cuando sea necesario.
    """  
    criteriosDeCalificacion = """
    Criterios por tipo de pregunta (decide true/false para cada respuesta):

    1) SINGLESELECTION
    - Se considera correcta si la respuesta coincide EXACTAMENTE con la opción válida.
    - Si existe 'correctOptionIndex', usarlo; si existe 'correctOption' usarlo.
    - Si no hay forma explícita de saber la correcta, marcar false (formato insuficiente).
    2) FREERESPONSE
    - Extrae de 'description' (o campos específicos si existen) las:
        • Palabras clave obligatorias: todas deben aparecer (insensible a mayúsculas/minúsculas, acepta variantes simples sing/plural).
        • Palabras clave prohibidas: ninguna debe aparecer.
    - Longitud razonable: no vacía y no exceder 3–4 veces lo esperado según la descripción.
    - Marca true solo si cumple 100% obligatorias, 0 prohibidas y coherencia mínima (no contradice el enunciado).
    3) FIXTHECODE
    - El usuario debe proponer código corregido (respuesta no vacía y con bloques de código o texto técnico).
    - Evalúa según lo indicado en 'description':
        • Errores mencionados: cada uno debe estar corregido (nombres, lógica, sintaxis).
        • Si se listan pruebas I/O: cada prueba (entrada -> salida esperada) debe cumplirse.
    - Si falta corregir al menos un error crítico o falla alguna prueba, resultado false.
    4) COMPLETETHECODE
    - La respuesta debe indicar los tokens elegidos o el código final con los huecos llenos.
    - Solo acepta tokens provenientes de 'missingTokens'.
    - Coherencia sintáctica: el ensamblaje no debe producir errores de indentación ni sintaxis obvia.
    - Si la descripción define un objetivo (ej. función que retorna X), verificar que la solución lo cumpla.
    - Si cualquier token externo se usa sin justificación, marcar false.
    Reglas generales:
    - Ignora explicaciones extensas irrelevantes.
    - Si una respuesta está vacía o es claramente fuera de contexto, false.
    - No inventes criterios que no estén insinuados en la pregunta/description.
    """
    formatoEvaluacion = r"""
    FORMATO JSON DE SALIDA (estricto):
    - Devuelve SOLO un objeto JSON válido (application/json).
    - No uses Markdown, no uses comillas invertidas/backticks (```), no incluyas texto fuera del objeto.
    - No uses null ni arrays vacíos para campos opcionales: omite el campo si no aplica.
    - Campos:
        {
                "questionsResults": [true, false, ...],
                "resultType": "APPROVED" | "DISAPPROVED" | "FULLYAPPROVED",
                "score": 0
        }
    Reglas:
    - questionsResults: boolean por cada pregunta en orden.
    - score = aciertos / total (int max 5).
    - FULLYAPPROVED: 100% correctas.
    - APPROVED: >= 60% y < 100%.
    - DISAPPROVED: < 60%.
    """
    reglas = """
    REGLAS IMPORTANTES:
    - Responde SOLO con el objeto JSON válido siguiendo el formato anterior.
    - NO incluyas ``` ni etiquetas de lenguaje ni comentarios.
    """
    contexto = f"""
    Preguntas: {json.dumps(encode(preguntas), ensure_ascii=False)}
    Respuestas del usuario: {json.dumps(encode(respuestas), ensure_ascii=False)}
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
    def __init__(self,preguntas: List[dict], respuestas: List[dict] = []):
        self.llm = obtenerModelo()
        self.AgenteEvaluador = AgenteEvaluador(
            llm=self.llm,
            contexto=PromptEvaluador(preguntas, respuestas),
            tools=[BC_Tool()],
        )
        
    async def evaluarRespuestas(self):
        return await self.AgenteEvaluador.responder("Evalúa las respuestas proporcionadas según las preguntas dadas en el FORMATO JSON indicado. Responde SOLO con el JSON válido, sin texto adicional, comentarios ni explicaciones fuera del objeto.")
        