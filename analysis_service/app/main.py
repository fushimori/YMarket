from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from api.routes import router
from config.settings import settings
from consumers.kafka_consumer import KafkaLogConsumer
from storage.index_manager import IndexManager
from storage.elastic_client import ElasticClient
from metrics import api_metrics, metrics_endpoint
import asyncio
import logging
import jwt

app = FastAPI(
    title="Analysis Service",
    description="Сервис для сбора и анализа логов, метрик и трейсов",
    version="1.0.0"
)

app.include_router(router)

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
@api_metrics()
async def protected_route(current_user: str = Depends(get_current_user)):
    return {"message": f"Hello, {current_user}!"}

@app.on_event("startup")
@api_metrics()
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
    
    # Закомментируем запуск Kafka consumer
    # try:
    #     # Запуск Kafka consumer
    #     consumer = KafkaLogConsumer()
    #     await consumer.start()
    # except Exception as e:
    #     logging.error(f"Failed to start Kafka consumer: {str(e)}")
    #     raise

@app.on_event("shutdown")
@api_metrics()
async def shutdown_event():
    """
    Остановка потребителя при завершении работы приложения
    """
    # Закомментируем остановку Kafka consumer
    # try:
    #     # Остановка Kafka consumer
    #     consumer = KafkaLogConsumer()
    #     await consumer.stop()
    # except Exception as e:
    #     logging.error(f"Failed to stop Kafka consumer: {str(e)}")
    #     raise

@app.get("/health")
@api_metrics()
async def health_check():
    """
    Проверка работоспособности сервиса
    """
    return {"status": "healthy"} 

@app.get("/metrics")
async def get_metrics():
    """
    Получение метрик сервиса
    """
    return await metrics_endpoint()