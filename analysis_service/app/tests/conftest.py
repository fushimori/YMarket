import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from elasticsearch import AsyncElasticsearch
from aiokafka import AIOKafkaProducer
import json
from main import app
from config.settings import settings
from datetime import datetime, timedelta

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest_asyncio.fixture
async def elastic_client():
    """Фикстура для тестового клиента Elasticsearch"""
    client = AsyncElasticsearch(
        [f"http://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"],
        basic_auth=(
            settings.ELASTICSEARCH_USERNAME,
            settings.ELASTICSEARCH_PASSWORD
        ) if settings.ELASTICSEARCH_USERNAME else None
    )
    try:
        # Очищаем все индексы перед тестами
        await client.indices.delete(index="logs-*", ignore=[404])
        
        # Создаем индекс с правильным маппингом
        await client.indices.create(
            index="logs-test_service",
            body={
                "mappings": {
                    "properties": {
                        "level": {"type": "keyword"},
                        "timestamp": {"type": "date"},
                        "service": {"type": "keyword"},
                        "message": {"type": "text"},
                        "error_message": {"type": "text"},
                        "error_type": {"type": "keyword"},
                        "stack_trace": {"type": "text"},
                        "metadata": {"type": "object"}
                    }
                }
            },
            ignore=[400]  # Игнорируем ошибку, если индекс уже существует
        )
        
        yield client
    finally:
        # Очищаем все индексы после тестов
        await client.indices.delete(index="logs-*", ignore=[404])
        await client.close()

@pytest_asyncio.fixture
async def kafka_producer():
    """Фикстура для тестового Kafka producer"""
    producer = AIOKafkaProducer(
        bootstrap_servers=settings.KAFKA_BROKERS,
        value_serializer=lambda x: json.dumps(x).encode('utf-8')
    )
    try:
        await producer.start()
        yield producer
    finally:
        await producer.stop() 