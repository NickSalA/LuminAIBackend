# Utilitario para crear tool de base de conocimientos
from langchain_core.tools import create_retriever_tool

# Manejo de herramientas y agentes
from langchain_core.tools import Tool

# Helpers propios
from src.util.util_retriever import obtenerBaseDeConocimientos

retriever = obtenerBaseDeConocimientos()

def BC_Tool() -> Tool:
    return create_retriever_tool(
        retriever=retriever,
        name="BaseDeConocimientos",
        description=(
            "Eres BC_Tool. Sólo puedes buscar y devolver fragmentos de la base de conocimiento."
            "No inventes contenido. Devuelve texto y metadatos de la fuente."
            "Si no encuentras resultados relevantes, responde vacío."
        ),
    )