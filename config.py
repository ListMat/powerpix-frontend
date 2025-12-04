from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from dotenv import load_dotenv
import os

# Carregar .env explicitamente
load_dotenv()


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "")
    WEBHOOK_PATH: str = os.getenv("WEBHOOK_PATH", "/webhook")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "senha_forte")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///powerpix.db")
    VALOR_APOSTA: float = float(os.getenv("VALOR_APOSTA", "5.00"))
    
    # Asaas Configuration
    ASAAS_API_KEY: str = os.getenv("ASAAS_API_KEY", "")
    ASAAS_API_URL: str = os.getenv("ASAAS_API_URL", "https://api.asaas.com/v3")
    ASAAS_WEBHOOK_TOKEN: str = os.getenv("ASAAS_WEBHOOK_TOKEN", "")  # Token para validar webhooks


@lru_cache()
def get_settings() -> Settings:
    return Settings()

