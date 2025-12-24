from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://ars:ars@localhost:5432/ars"
    app_name: str = "Registry Service"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        fields = {
            "database_url": {"env": "REGISTRY_DATABASE_URL", "env_prefix": ""},
        }


settings = Settings()

