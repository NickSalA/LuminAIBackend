# Utilitario para crear y ejecutar agentes
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent

# Utilitario para el modelo de lenguaje
from langchain_google_genai import ChatGoogleGenerativeAI

# Manejo de memoria del agente
from langgraph.checkpoint.memory import InMemorySaver

# Manejo de prompts
from langchain_core.prompts import ChatPromptTemplate

def crearAgente(
    llm: ChatGoogleGenerativeAI, contexto: ChatPromptTemplate, tools: list | None = None, memoria=None
):
    if tools is None:
        tools = []
    if memoria is None:
        memoria = InMemorySaver()
    agente = create_react_agent(
        model=llm, tools=tools, checkpointer=memoria, prompt=contexto,
    )
    return agente

def ejecutar(agente, consulta: str = "", config=None, verbose: bool = True):
    try:
        respuesta = agente.invoke({"messages": [{"role": "user", "content": consulta}]}, config=config)
        if not verbose:
            return respuesta
        return respuesta["messages"][-1].content
    except Exception as e:
        raise Exception(f'Error en la ejecución del agente: {e}')
