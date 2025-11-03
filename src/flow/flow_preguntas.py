from src.agents.agente_evaluador import AgenteEvaluador
from src.util.util_llm import obtenerModelo
from langchain_core.prompts import ChatPromptTemplate
from src.tools.tool_buscar_base_conocimientos import BC_Tool

def PromptEvaluador(seccion: dict):
    seccion = seccion or {}
    tema = seccion.get("tema", "Sin tema")
    lenguaje = seccion.get("lenguaje", "Python")
    nivel = seccion.get("nivel", "básico")
    
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
    Eres 'GeneradorAI', un asistente que crea prácticas de programación con 5 preguntas.
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
    FORMATO JSON DE SALIDA (único y obligatorio):
    {
    "preguntas": [
        {
            "id": "<id_unico>",
            "tipo": "seleccion_unica" | "respuesta_libre" | "arregla_codigo" | "completa_codigo",
            "enunciado": "<texto conciso>",
            "codigo_inicial": "<string con \\n escapado si aplica>",
            "opciones": ["<op1>", "<op2>", "<op3>", "<op4>"] // solo si el tipo lo requiere
        }
    ]
    }

    DETALLES POR TIPO:
    - seleccion_unica:
        • Incluye 4 opciones exactamente.
        • El campo 'opciones' debe existir.
        • El usuario elegirá una de las 4 (texto o índice).

    - respuesta_libre:
        • No incluye 'opciones'.
        • El usuario escribirá una explicación corta.

    - arregla_codigo:
        • No incluye 'opciones'.
        • 'codigo_inicial' contiene un error claro (sintaxis, indentación o lógica simple).

    - completa_codigo:
        • Incluye 'opciones' con 4 fragmentos de código.
        • El usuario debe ordenar o seleccionar los fragmentos correctos.
    """
    )
    
    instrucciones = """
    Genera la práctica ahora para el tema y nivel dados. Responde SOLO con el JSON válido siguiendo el formato anterior.
    """    
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", informacionSeccion),
        ("system", identidad),
        ("system", formatoTipos),
        ("system", formatoJSON),
        ("system", instrucciones),
    ])

    return prompt

class FlowAgentePreguntas:
    def __init__(self, seccion: dict):
        self.llm = obtenerModelo()
        self.AgenteEvaluador = AgenteEvaluador(
            llm=self.llm,
            contexto=PromptEvaluador(seccion),
            tools=[BC_Tool()],
        )
    def evaluarRespuesta(self, mensaje: str = ""):
        return self.AgenteEvaluador.responder(mensaje)