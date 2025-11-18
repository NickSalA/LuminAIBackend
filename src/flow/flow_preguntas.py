from src.agents.agente_evaluador import AgenteEvaluador
from src.util.util_llm import obtenerModelo
from src.tools.tool_buscar_base_conocimientos import BC_Tool

def PromptEvaluador(seccion: dict) -> str:
    levelName = seccion.get("", "Introducción al JSON")
    sectionName = seccion.get("", "Reglas de sintaxis para objetos y arrays JSON.")
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
    Eres un asistente que crea prácticas de programación con 5 preguntas a partir del tema "{sectionName}".
    Reglas:
    - TODO en español.
    - Solo código y ejemplos en {lenguaje}.
    - EXACTAMENTE 5 preguntas por práctica.
    - Determina la dificultad según el nivel del tema "{levelName}".
    - Usa únicamente estos tipos: SingleSelection, FreeResponse, FixTheCode, CompleteTheCode.
    - Debe haber al menos 1 pregunta de cada tipo; la quinta puede ser cualquiera.
    - Sé claro y conciso en enunciados y explicaciones.
    """
    )

    formatoTipos = """
    Requisitos por tipo:
    1) SingleSelection
    - Campos: question, description, options (exactamente 4).
    - Enunciado con una sola respuesta correcta y opciones plausibles de longitud similar.
    - Evita pistas, ambigüedades y explicaciones dentro de las opciones.
    - No incluyas marcas de corrección en el JSON (solo las 4 opciones).

    2) FreeResponse
    - Campos: question, description.
    - En 'description' indica criterios de evaluación:
        • Palabras clave obligatorias.
        • Elementos a evitar (si aplica).
        • Rúbrica breve (2–3 criterios).
    - Respuesta esperada corta y verificable.

    3) FixTheCode
    - Campos: question, description, wrongCode.
    - 'wrongCode' debe contener errores concretos (sintaxis, lógica, nombres, casos borde).
    - En 'description' define comportamiento esperado y, si aplica, 1–2 pruebas I/O simples (entrada → salida).
    - No agregues campos adicionales ni comentarios en el JSON.
    
    4) CompleteTheCode
    - Incluye 'codeLines' con uno o más tokens 'MISSING' donde falta código.
    - Incluye 'missingTokens' con EXACTAMENTE 4 opciones de tokens/fragmentos para completar.
    - Incluye 'description' explicando el objetivo del código incompleto.
    
    Especificación de 'codeLines':
    - Campos: question, description, codeLines, missingTokens (exactamente 4).
    - 'codeLines' es un array de líneas. Cada línea es un objeto con:
        { "tokens": [ { "token": "<string|INDENT|MISSING|...>" }, ... ] }
    - Tokens especiales permitidos:
        • INDENT: indica aumento de indentación en esa línea.
        • MISSING: indica un hueco a completar en CompleteTheCode.
    - 'missingTokens': 4 piezas (tokens o fragmentos cortos) coherentes con los MISSING.
    - En 'description' aclara el objetivo y, si hay varias soluciones válidas, menciónalo.
    - No incluyas comentarios en el JSON.

    Ejemplo ilustrativo de 'codeLines' (solo como guía, NO es parte de la salida):
    "codeLines": [
        { "tokens": [ { "token": "def" }, { "token": "main" }, { "token": "(" }, { "token": ")" }, { "token": ":" } ] },
        { "tokens": [ { "token": "INDENT" }, { "token": "print" }, { "token": "(" }, { "token": "MISSING" }, { "token": ")" } ] }
    ]
    """

    formatoJSON = (r"""
    FORMATO JSON DE SALIDA (estricto):
    - Devuelve SOLO un objeto JSON válido (application/json).
    - No uses Markdown, no uses comillas invertidas/backticks (```), no incluyas texto fuera del objeto.
    - No uses null ni arrays vacíos para campos opcionales: omite el campo si no aplica.
    - Campos:
        {
            "questions":[
                {
                    // Campos comunes:
                    "id": "<id_unico>", // 1, 2, 3, 4, 5
                    "type": "SINGLESELECTION" | "FREERESPONSE" | "FIXTHECODE" | "COMPLETETHECODE",
                    "description": "<texto conciso>", // str
                    
                    // Para SingleSelection:
                    "options": ["<op1>", "<op2>", "<op3>", "<op4>"], // array de str (exactamente 4 opciones)
                    
                    // Para SingleSelection y FreeResponse:
                    "question": "<texto de la pregunta>", // str
                    
                    // Para FixTheCode:
                    "wrongCode": "<Texto con errores>", // str
                    
                    // Para CompleteTheCode:
                    "codeLines": [], // array de líneas con tokens
                    "missingTokens": ["<tok1>", "<tok2>", "<tok3>", "<tok4>"]
                }
            ]
        }
    - Validación:
        • EXACTAMENTE 5 preguntas.
        • Al menos 1 de cada tipo.
    """
    )
    
    instrucciones = """
    Genera la práctica ahora para el tema y nivel dados.
    Responde SOLO con el objeto JSON válido siguiendo el formato anterior.
    NO incluyas ``` ni etiquetas de lenguaje ni comentarios.
    """

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