from langchain_google_genai import ChatGoogleGenerativeAI

from src.util.util_credenciales import obtenerAPI

def obtenerModelo() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        api_key=obtenerAPI("CONF-GOOGLE-API-KEY"),
    )

