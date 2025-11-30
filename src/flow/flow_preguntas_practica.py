# Flujo para generar preguntas de práctica

# Importa el agente evaluador
from src.agents.agente_evaluador import AgenteEvaluador

# Importa el modelo de lenguaje
from src.util.util_llm import obtenerModelo

# Importa la herramienta para buscar en la base de conocimientos
from src.tools.tool_buscar_base_conocimientos import BC_Tool

def PromptEvaluador(seccion: dict) -> str:
    levelName = seccion.get("levelName", "Introducción al JSON")
    sectionName = seccion.get("sectionName", "Reglas de sintaxis para objetos y arrays JSON.")
    lenguaje = "Python"
    
    informacionSeccion = (
        f"""
        INFORMACIÓN DE LA SECCIÓN:
            - Nivel: {levelName}
            - Tema: {sectionName}
            - Lenguaje: {lenguaje}
        """
    )

    identidad = (
        f"""
    Eres un asistente experto en {lenguaje}. Crea una práctica de 5 preguntas sobre "{sectionName}" (Nivel: {levelName}).
    Reglas:
    1. Salida: ÚNICAMENTE JSON válido. Sin markdown, sin comentarios.
    2. Idioma: Español. Código en {lenguaje}.
    3. Cantidad: Exactamente 5 preguntas.
    4. Tipos: Al menos una de cada: SingleSelection, FreeResponse, FixTheCode, CompleteTheCode.
    5. Concisión: Sé muy breve y directo. Las opciones de respuesta deben tener máximo 3 palabras. No incluyas comentarios en el código. En CompleteTheCode usa a lo mucho 5 o 6 "tokens".
    """
    )
    
    formatoTipos = """
    Tipos de preguntas:
    - SingleSelection: "options" (4 strings), una correcta. Sin pistas obvias. 
    - FreeResponse: Sin campos adicionales especificos.
    - FixTheCode: "wrongCode" con errores. 
    - CompleteTheCode: "codeLines" es un array de líneas. Cada línea tiene "tokens". 
      Reglas para tokens:
      1. NO generes tokens vacíos ("").
      2. Separa la lógica (ej: "var", "=", "val" son 3 tokens distintos).
      3. Usa "INDENT" solo al inicio de la línea para sangría.
      4. Usa "MISSING" donde el usuario debe completar.
      5. "missingTokens" NO DEBE TENER DUPLICADOS. Oculta elementos diferentes (ej: una variable y un operador, no dos veces "=").
      6. La cantidad de elementos en "missingTokens" DEBE SER EXACTAMENTE IGUAL a la cantidad de "MISSING" en "codeLines".
      7. Mínimo deben ser 2 "MISSING" y por defecto 2 "missingTokens"
      8. No uses "INDENT" en "missingTokens".
      9. Has breves los "tokens".
    """

    formatoJSON = (r"""
    Estructura JSON requerida:
    {
        "questions": [
            {
                "id": 1,
                "type": "SINGLESELECTION" | "FREERESPONSE" | "FIXTHECODE" | "COMPLETETHECODE",
                "question": "Enunciado...",
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

class FlowAgentePreguntas:
    def __init__(self, seccion: dict):
        self.llm = obtenerModelo()
        self.AgenteEvaluador = AgenteEvaluador(
            llm=self.llm,
            contexto=PromptEvaluador(seccion),
            tools=[BC_Tool()],
        )
    async def generarPreguntas(self):
        return await self.AgenteEvaluador.responder("Genera AHORA la práctica con EXACTAMENTE 5 preguntas en el FORMATO JSON indicado. Responde SOLO con el JSON válido, sin texto adicional, comentarios ni explicaciones fuera del objeto.")