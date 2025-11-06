from src.agents.agente_evaluador import AgenteEvaluador
from src.util.util_llm import obtenerModelo
from src.tools.tool_buscar_base_conocimientos import BC_Tool

def PromptEvaluador(seccion: dict) -> str:
    seccion = seccion or {}
    tema = seccion.get("tema", "Introducción a If y Bucles")
    lenguaje = "Python"
    nivel = seccion.get("nivel", "Básico")
    
    informacionSeccion = (
        f"""
        INFORMACIÓN DE LA SECCIÓN:
            - Tema: {tema}
            - Lenguaje: {lenguaje}
            - Nivel: {nivel}
        """
    )

    identidad = (
        f"""
    Eres un asistente que crea prácticas de programación con 5 preguntas.
    Reglas:
    - TODO en español.
    - Solo código y ejemplos en Python.
    - Dificultad coherente con el nivel (básico/intermedio/avanzado).
    - EXACTAMENTE 5 preguntas por práctica.
    - Usa únicamente estos tipos: seleccion_unica, respuesta_libre, arregla_codigo, completa_codigo.
    - Debe haber al menos 1 pregunta de cada tipo; la quinta puede ser cualquiera.
    - Sé claro y conciso en enunciados y explicaciones.
    """
    )

    formatoTipos = """
    Requisitos por tipo:
    1) seleccion_unica
    - 4 opciones exactamente y 1 correcta (este es el único caso con respuesta única).
    2) respuesta_libre
    - No usa 'opciones'. Define criterios basados en palabras clave obligatorias/prohibidas, sinónimos, y una rúbrica breve.
    3) arregla_codigo
    - Incluye 'codigo_inicial' con errores específicos. Define pruebas de verificación (I/O) y/o reglas AST simples.
    4) completa_codigo
    - Incluye 'codigo_inicial' y 4 'opciones' fragmento. Permite múltiples órdenes/ensambles válidos mediante 'ordenes_validas' o reglas.
    """

    formatoJSON = (r"""
    FORMATO JSON DE SALIDA (estricto):
    - Devuelve SOLO un objeto JSON válido (application/json).
    - No uses Markdown, no uses comillas invertidas/backticks (```), no incluyas texto fuera del objeto.
    - No uses null ni arrays vacíos para campos opcionales: omite el campo si no aplica.
    - Campos:
        {
            "preguntas": [
                {
                    "id": "<id_unico>", // q1, q2, q3, q4, q5
                    "tipo": "seleccion_unica" | "respuesta_libre" | "arregla_codigo" | "completa_codigo",
                    "enunciado": "<texto conciso>",
                    "codigo_inicial": "<string con \\n escapado si aplica>",
                    "opciones": ["<op1>", "<op2>", "<op3>", "<op4>"] // solo si el tipo lo requiere
                }
            ]
        }
    - Validación:
        • EXACTAMENTE 5 preguntas.
        • Al menos 1 de cada tipo.
        • 'respuesta_libre' y 'arregla_codigo' NO incluyen 'opciones'.
        • 'completa_codigo' y 'seleccion_unica' SÍ incluyen 'opciones' (exactamente 4).
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
    def generarPreguntas(self):
        return self.AgenteEvaluador.responder("Genera AHORA la práctica con EXACTAMENTE 5 preguntas en el FORMATO JSON indicado. Responde SOLO con el JSON válido, sin texto adicional, comentarios ni explicaciones fuera del objeto.")
