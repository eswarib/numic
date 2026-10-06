from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_prefix": "NUMIC_"}

    database_url: str = "postgresql+asyncpg://localhost/numic"
    database_echo: bool = False
