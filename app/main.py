import uvicorn
from fastapi import FastAPI
from app.config import settings

app = FastAPI(
    title=settings.app_name,
    debug=settings.debug
)

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