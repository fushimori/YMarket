from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from api.routes import router
from config.settings import settings
from consumers.kafka_consumer import KafkaLogConsumer
from storage.index_manager import IndexManager
from storage.elastic_client import ElasticClient
import asyncio
import logging
import jwt

app = FastAPI(
    title="Analysis Service",
    description="Сервис для сбора и анализа логов, метрик и трейсов",
    version="1.0.0"
)

app.include_router(router, prefix="/api/v1")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return email
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

@app.get("/api/v1/protected")
async def protected_route(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello, {current_user}!"}

@app.on_event("startup")
async def startup_event():
    """
    Запуск потребителя при старте приложения
    """
    try:
        # Инициализация политики хранения
        index_manager = IndexManager()
        await index_manager.setup_index_lifecycle()
    except Exception as e:
        logging.error(f"Failed to initialize index manager: {str(e)}")
        raise
    
    try:
        # Запуск Kafka consumer
        consumer = KafkaLogConsumer()
        await consumer.start()
    except Exception as e:
        logging.error(f"Failed to start Kafka consumer: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """
    Остановка потребителя при завершении работы приложения
    """
    try:
        # Остановка Kafka consumer
        consumer = KafkaLogConsumer()
        await consumer.stop()
    except Exception as e:
        logging.error(f"Failed to stop Kafka consumer: {str(e)}")
        raise

@app.get("/health")
async def health_check():
    """
    Проверка работоспособности сервиса
    """
    return {"status": "healthy"} 