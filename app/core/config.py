"""
Configuración centralizada de la aplicación.

Java equivalent: application.properties + @ConfigurationProperties

pydantic-settings lee las variables de un archivo .env automáticamente.
Si una variable no está en .env, usa el valor por defecto definido aquí.

Ejemplo de .env:
    SECRET_KEY=mi-clave-secreta-super-larga
    DATABASE_URL=postgresql+asyncpg://user:pass@localhost/hvac_saas
    DEBUG=false
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── JWT ─────────────────────────────────────────────────────────────────
    # Clave para firmar los tokens. CAMBIAR en producción con una cadena aleatoria larga.
    SECRET_KEY: str = "cambiar-en-produccion-usar-variable-de-entorno"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 horas

    # ── Base de datos ────────────────────────────────────────────────────────
    # SQLite para desarrollo local (sin Docker, archivo en disco)
    # En producción cambiar a: postgresql+asyncpg://user:password@localhost:5432/hvac_saas
    DATABASE_URL: str = "sqlite+aiosqlite:///./hvac_saas.db"

    # ── App ──────────────────────────────────────────────────────────────────
    APP_NAME: str = "CRM FRIGO"
    DEBUG: bool = True  # False en producción — deja de imprimir SQL en consola

    # Lee el archivo .env si existe (no falla si no existe)
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


# Instancia única — se importa en todo el proyecto como: from app.core.config import settings
settings = Settings()
