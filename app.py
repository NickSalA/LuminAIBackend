from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

import uvicorn

from src.api.agents.agents_api import routerAgente
from src.api.usuarios_api import routerUsuarios
from src.api.contenido_api import routerContenido

app = FastAPI(title="LuminAI API")

app.include_router(routerAgente, prefix="/agente", tags=["Agente"])
app.include_router(routerUsuarios, tags=["Autentificacion"])
app.include_router(
    router=routerContenido,
    prefix="/api",
    tags=["Contenido"]
)

ALLOWED_ORIGINS = [
    "http://0.0.0.0:8000",
    "http://127.0.0.1:8000"
    ]

# CORS (ajusta origins a tu front real)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cookie de sesión
app.add_middleware(
    SessionMiddleware,
    secret_key="cambia-esto-en-prod",
    same_site="lax",
    https_only=True,   # pon True en producción HTTPS
    # session_cookie="support_session",
)

@app.get("/")
def home():
    return {"ok": True, "msg": "API de IA activa. Usa POST /agente/tutor"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)