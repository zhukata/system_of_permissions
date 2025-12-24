from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database (тот же Postgres, что и у ARS)
    database_url: str = "postgresql://ars:ars@localhost:5432/ars"

    # RabbitMQ
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_vhost: str = "/"

    # Registry Service (source of truth)
    registry_service_url: str = "http://localhost:8001"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        fields = {
            "registry_service_url": {"env": "REGISTRY_SERVICE_URL"},
        }

    @property
    def rabbitmq_url(self) -> str:
        return (
            f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}"
            f"@{self.rabbitmq_host}:{self.rabbitmq_port}{self.rabbitmq_vhost}"
        )


settings = Settings()

