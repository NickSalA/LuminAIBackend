# Utilitario para crear tool de base de conocimientos
from langchain_core.tools.retriever import create_retriever_tool

# Manejo de herramientas y agentes
from langchain_core.tools import Tool

# Helpers propios
from src.util.util_retriever import obtenerBaseDeConocimientos

retriever = obtenerBaseDeConocimientos()

def BC_Tool() -> Tool:
    
    def buscar_documentos_wrapper(query: str) -> str:
        docs = retriever.invoke(query)
        return "\n\n".join([d.page_content for d in docs])
    
    return Tool.from_function(
        func=buscar_documentos_wrapper,
        name="BaseDeConocimientos",
        description=(
            "Eres BC_Tool. Sólo puedes buscar y devolver fragmentos de la base de conocimiento."
            "No inventes contenido. Devuelve texto y metadatos de la fuente."
            "Si no encuentras resultados relevantes, responde vacío."
        ),
    )