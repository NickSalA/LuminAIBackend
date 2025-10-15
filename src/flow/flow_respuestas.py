from src.agents.agente_evaluador import AgenteEvaluador
from src.util.util_llm import obtenerModelo
from langchain_core.prompts import ChatPromptTemplate
from src.tools.tool_buscar_base_conocimientos import BC_Tool

def PromptEvaluador(seccion: dict, mensaje: str = ""):
    seccion = seccion or {}
    tema = seccion.get("tema", "Tema no especificado")
    nivel = seccion.get("nivel", "Nivel no especificado")
    lenguaje = seccion.get("lenguaje", "Lenguaje no especificado")
        
    identidad = (
        f"""
        Eres un asistente virtual llamado 'EvaluadorAI' especializado en evaluar la calidad de las respuestas proporcionadas por otros agentes.
        Tu objetivo es analizar las respuestas y proporcionar una evaluación detallada basada en criterios como precisión, relevancia, claridad y utilidad.
        Eres objetivo, profesional y siempre buscas proporcionar retroalimentación constructiva.
        """
    )
    
    
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", identidad),
    ])

    return prompt

class FlowAgenteRespuestas:
    def __init__(self,seccion: dict, mensaje: str = ""):
        self.llm = obtenerModelo()
        self.AgenteEvaluador = AgenteEvaluador(
            llm=self.llm,
            contexto=PromptEvaluador(seccion, mensaje),
            tools=[BC_Tool()],
        )
    def evaluarRespuesta(self, mensaje: str = ""):
        return self.AgenteEvaluador.responder(mensaje)