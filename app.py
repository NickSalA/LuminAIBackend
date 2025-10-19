from fastapi import FastAPI

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

app.include_router(agents_get_router, prefix="/agents", tags=[""])
app.include_router(routerUsuarios, tags=["Autentificacion"])

@app.get("/")
def home():
    return {"ok": True, "msg": "API de IA activa. Usa POST /user/chat"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True, log_level="info")