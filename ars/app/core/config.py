from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://ars:ars@localhost:5432/ars"
    
    rabbitmq_host: str = "localhost"
    rabbitmq_port: int = 5672
    rabbitmq_user: str = "guest"
    rabbitmq_password: str = "guest"
    rabbitmq_vhost: str = "/"
    
    registry_service_url: str = "http://localhost:8001"
    
    app_name: str = "Access Request Service"
    
    @property
    def rabbitmq_url(self) -> str:
        """Возвращает URL для подключения к RabbitMQ."""
        return f"amqp://{self.rabbitmq_user}:{self.rabbitmq_password}@{self.rabbitmq_host}:{self.rabbitmq_port}{self.rabbitmq_vhost}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        fields = {
            "registry_service_url": {"env": "REGISTRY_SERVICE_URL"},
        }


settings = Settings()

