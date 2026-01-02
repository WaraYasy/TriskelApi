from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "Triskel-API"
    debug: bool = True
    port: int = 8000

    # Firebase
    firebase_credentials_path: str = "config/firebase-credentials.json"

    class Config:
        env_file = ".env"

settings = Settings()