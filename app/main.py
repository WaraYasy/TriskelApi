import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import players, games
from app.firebase import firebase_manager

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

# CORS - Permitir peticiones desde cualquier origen (ajustar en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar Firebase al arrancar
@app.on_event("startup")
def startup_event():
    firebase_manager.initialize()

# Incluir rutas
app.include_router(players.router)
app.include_router(games.router)

@app.get("/")
def read_root():
    return {
        "message": "Bienvenido a Triskel-API",
        "status": "online"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.port, reload=settings.debug)