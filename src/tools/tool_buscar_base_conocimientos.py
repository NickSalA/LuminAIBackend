# Manejo de herramientas y agentes
from langchain_core.tools import Tool

# Helpers propios
from src.util.util_retriever import obtenerBaseDeConocimientos

# Utilitario para crear tool de base de conocimientos
from src.util.util_base_conocimientos import create_retriever_tool

retriever = obtenerBaseDeConocimientos()

def BC_Tool() -> Tool:
    
    return create_retriever_tool(
        retriever=retriever,
        name="BC_Tool",
        description="Úsala para responder preguntas técnicas específicas sobre los contenidos de programación disponibles en la base de conocimientos. Devuelve respuestas precisas y concisas basadas en los documentos que encuentres.",
    )