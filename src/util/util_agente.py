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
    agente = create_agent(
        model=llm, tools=tools, checkpointer=memoria if memoria else InMemorySaver(), system_prompt=contexto,
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

async def ejecutar(agente, consulta: str = "", config=None, verbose: bool = True):
    payload = {"messages": [{"role": "user", "content": consulta}]}
    
    respuesta = await agente.ainvoke(payload, config=config)
    try:
        if not verbose:
            return respuesta
        respuesta = respuesta["messages"][-1].content
        
        if isinstance(respuesta, str):
            return respuesta
        
        respuesta = respuesta[0].get("text", "")
        
        return respuesta
    except Exception as e:
        raise Exception(f'Error en la ejecución del agente: {e}')

async def ejecutarSinMemoria(agente, consulta: str = "", verbose: bool = True):
    payload = {"messages": [{"role": "user", "content": consulta}]}
    
    respuesta = await agente.ainvoke(payload)
    try:
        if not verbose:
            return respuesta
        respuesta = respuesta["messages"][-1].content
        respuesta = respuesta[0].get("text", "").replace("```json", "").replace("```", "")
        if not respuesta:
            respuesta = str(respuesta)
        return json.loads(respuesta)
    except json.JSONDecodeError as je:
        raise Exception(f'Error al decodificar JSON: {je}')
    except Exception as e:
        raise Exception(f'Error en la ejecución del agente: {e}')
    