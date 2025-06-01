from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # Основные настройки
    SERVICE_NAME: str = "analysis_service"
    DEBUG: bool = False
    
    # Kafka настройки
    KAFKA_BROKERS: List[str] = ["kafka:9092"]
    KAFKA_CONSUMER_GROUP: str = "analysis_service_group"
    
    # Elasticsearch настройки
    ELASTICSEARCH_HOST: str = "elasticsearch"
    ELASTICSEARCH_PORT: int = 9200
    ELASTICSEARCH_USERNAME: Optional[str] = None
    ELASTICSEARCH_PASSWORD: Optional[str] = None
    
    # API настройки
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8006
    
    class Config:
        env_file = ".env"

settings = Settings() 