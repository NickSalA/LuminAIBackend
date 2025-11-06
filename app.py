from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from src.util.util_checkpointer import obtenerConexionCheckpointer

from contextlib import asynccontextmanager

import uvicorn

from src.api.agents.agents_get import agents_get_router

from src.api.usuarios_api import routerUsuarios

@asynccontextmanager
async def lifespan(app: FastAPI):
    conn, saver = obtenerConexionCheckpointer() 
    app.state.conn = conn
    app.state.checkpointer = saver
    print("Checkpointer listo:", type(saver).__name__ if saver else None)
    try:
        yield
    finally:
        try:
            if getattr(app.state, "conn", None) is not None:
                app.state.conn.__exit__(None, None, None)  # #type: ignore
        except Exception:
            pass

app = FastAPI(title="LuminAI API", lifespan=lifespan)

app.include_router(agents_get_router, prefix="/agente", tags=["Agente"])
app.include_router(routerUsuarios, tags=["Autentificacion"])

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
    https_only=False,   # pon True en producción HTTPS
    # session_cookie="support_session",
)

@app.get("/")
def home():
    return {"ok": True, "msg": "API de IA activa. Usa POST /agente/tutor"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)