# Flujo para generar preguntas de práctica

# Importa el agente evaluador
from src.agents.agente_evaluador import AgenteEvaluador

# Importa el modelo de lenguaje
from src.util.util_llm import obtenerModelo

# Importa la herramienta para buscar en la base de conocimientos
from src.tools.tool_buscar_base_conocimientos import BC_Tool

def PromptEvaluador(sections: list[str]) -> str:
    sectionsName = ", ".join(sections)
    lenguaje = "Python"
    
    informacionSeccion = (
        f"""
        INFORMACIÓN DE LA SECCIÓN:
            - Tema: {sectionsName}
            - Lenguaje: {lenguaje}
        """
    )

    identidad = (
        f"""
    Eres un asistente que crea prácticas de programación con 5 preguntas a partir de los temas "{sectionsName}".
    Reglas:
    1. Salida: ÚNICAMENTE JSON válido. Sin markdown, sin comentarios.
    2. Idioma: Español. Código en {lenguaje}.
    3. Cantidad: Exactamente 5 preguntas.
    4. Tipos: Al menos una de cada: SingleSelection, FreeResponse, FixTheCode, CompleteTheCode.
    5. Concisión: Sé muy breve y directo. Las opciones de respuesta deben tener máximo 5 palabras. No incluyas comentarios en el código.
    """
    )
    
    formatoTipos = """
    Tipos de preguntas:
    - SingleSelection: "options" (4 strings), una correcta. Sin pistas obvias. 
    - FreeResponse: "description" incluye criterios de evaluación breves.
    - FixTheCode: "wrongCode" con errores. "description" describe qué debe hacer el código (funcionalidad esperada), SIN revelar la solución explícita.
    - CompleteTheCode: "codeLines" (array de objetos {"tokens": [{"token": "val"}]}). Usa tokens "MISSING" para huecos y "INDENT" para sangría. "missingTokens" lista las soluciones.
    """

    formatoJSON = (r"""
    Estructura JSON requerida:
    {
        "questions": [
            {
                "id": 1,
                "type": "SINGLESELECTION" | "FREERESPONSE" | "FIXTHECODE" | "COMPLETETHECODE",
                "question": "Enunciado...",
                "description": "Detalles/Rúbrica...",
                "options": ["...", "...", "...", "..."], // Solo SingleSelection
                "wrongCode": "...", // Solo FixTheCode
                "codeLines": [{"tokens": [{"token": "..."}]}], // Solo CompleteTheCode
                "missingTokens": ["..."] // Solo CompleteTheCode
            }
        ]
    }
    """)
    
    instrucciones = "Genera el JSON ahora."
    message = (
        informacionSeccion,
        identidad,
        formatoTipos,
        formatoJSON,
        instrucciones,
    )

    prompt = "\n".join(message)
    
    return prompt

class FlowAgentePreguntasDiarias:
    def __init__(self, sections: list[str]):
        self.llm = obtenerModelo()
        self.AgenteEvaluador = AgenteEvaluador(
            llm=self.llm,
            contexto=PromptEvaluador(sections),
            tools=[BC_Tool()],
        )
    async def generarPreguntas(self):
        return await self.AgenteEvaluador.responder("Genera AHORA la práctica con EXACTAMENTE 5 preguntas en el FORMATO JSON indicado. Responde SOLO con el JSON válido, sin texto adicional, comentarios ni explicaciones fuera del objeto.")