from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    APP_NAME: str = "Auxilios CECAR"
    DEBUG: bool = False
    DB_URL: str = "postgresql+asyncpg://auxilios_user:test1234@localhost:5432/auxilios_cecar"
    SECRET_KEY: str = "clave_temporal"
    TOKEN_EXPIRE_HOURS: int = 24
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_TLS: bool = True
    CORREO_DESTINO_BIENESTAR: str = "bienestar@cecar.edu.co"
    ANTHROPIC_API_KEY: str = ""
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:5500"]
    PROMEDIO_MINIMO: float = 3.7
    MAX_INTENTOS: int = 2
    DOMINIO_CORREO: str = "@cecar.edu.co"
    ADMIN_USUARIO: str = "admin"
    ADMIN_PASSWORD: str = "cecar2026admin"
    ADMIN_CORREO: str = "jeronimo.cajas@cecar.edu.co"
    ADMIN_CEDULA: str = "0000000"

    @property
    def DATABASE_URL(self) -> str:
        url = self.DB_URL
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    class Config:
        env_file = ".env"

settings = Settings()
