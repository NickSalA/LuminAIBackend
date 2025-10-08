from src.agents.agente_evaluador import AgenteEvaluador
from src.util.util_llm import obtenerModelo
from langchain_core.prompts import ChatPromptTemplate
from src.tools.tool_buscar_base_conocimientos import BC_Tool

def PromptEvaluador(seccion: dict):
    seccion = seccion or {}
    tema = seccion.get("tema", "Sin tema")
    lenguaje = seccion.get("lenguaje", "español")
    nivel = seccion.get("nivel", "básico")
    
    identidad = (
        f"""Eres un asistente virtual llamado 'EvaluadorAI' especializado en evaluar la calidad de las respuestas proporcionadas por otros agentes. 
        Tu objetivo es analizar las respuestas y proporcionar una evaluación detallada basada en criterios como precisión, relevancia, claridad y utilidad.
        Eres objetivo, profesional y siempre buscas proporcionar retroalimentación constructiva.
        """
    )
    
    formatoPregunta = (
        """
        
        """
    )
    
    formatoRespuesta = (
        """
        Proporciona una evaluación detallada de la respuesta dada, destacando sus fortalezas y áreas de mejora. 
        Asegúrate de ser específico y ofrecer ejemplos cuando sea posible.
        """
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", identidad),
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