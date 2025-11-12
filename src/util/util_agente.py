# Utilitario para crear y ejecutar agentes
from langchain.agents import create_agent

# Utilitario para el modelo de lenguaje
from langchain_google_genai import ChatGoogleGenerativeAI

# Manejo de memoria del agente
from langgraph.checkpoint.memory import InMemorySaver

# Manejo de JSON para respuestas estructuradas
import json

def crearAgente(
    llm: ChatGoogleGenerativeAI, contexto: str, tools: list | None = None, memoria=None
):
    if tools is None:
        tools = []
    if memoria is None:
        memoria = InMemorySaver()
    agente = create_agent(
        model=llm, tools=tools, checkpointer=memoria, system_prompt=contexto,
    )
    return agente

def crearAgenteSinMemoria(
    llm: ChatGoogleGenerativeAI, contexto: str, tools: list | None
):
    if tools is None:
        tools = []
    agente = create_agent(
        model=llm, tools=tools, system_prompt=contexto,
    )
    return agente

def ejecutar(agente, consulta: str = "", config=None, verbose: bool = True):
    payload = {"messages": [{"role": "user", "content": consulta}]}
    
    respuesta = agente.invoke(payload, config=config)
    try:
        if not verbose:
            return respuesta
        return respuesta["messages"][-1].content
    except Exception as e:
        raise Exception(f'Error en la ejecución del agente: {e}')

def ejecutarSinMemoria(agente, consulta: str = "", verbose: bool = True):
    payload = {"messages": [{"role": "user", "content": consulta}]}
    
    respuesta = agente.invoke(payload)
    try:
        if not verbose:
            return respuesta
        respuesta = respuesta["messages"][-1].content.replace("```json", "").replace("```", "")
        return json.loads(respuesta)
    except Exception as e:
        raise Exception(f'Error en la ejecución del agente: {e}')