import pytest
from datetime import datetime
from httpx import AsyncClient
from main import app
from storage.elastic_client import ElasticClient

@pytest.mark.asyncio
async def test_get_logs(test_client, elastic_client):
    # Подготовка тестовых данных
    test_log = {
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'test_service',
        'level': 'INFO',
        'message': 'Test log message',
        'metadata': {'test': 'data'}
    }
    
    # Сохраняем тестовый лог
    await elastic_client.index(
        index='logs-test_service',
        document=test_log
    )
    await elastic_client.indices.refresh(index='logs-test_service')
    
    # Тестируем API
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get('/api/v1/logs/test_service')
        assert response.status_code == 200
        logs = response.json()
        assert len(logs) > 0
        assert logs[0]['message'] == 'Test log message'

@pytest.mark.asyncio
async def test_get_error_logs(elastic_client):
    # Подготовка тестовых данных
    test_error = {
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'test_service',
        'level': 'ERROR',
        'error_type': 'TestError',
        'error_message': 'Test error message',
        'stack_trace': 'Test stack trace',
        'metadata': {'test': 'data'}
    }
    
    # Сохраняем тестовую ошибку
    await elastic_client.index(
        index='logs-test_service',
        document=test_error
    )
    await elastic_client.indices.refresh(index='logs-test_service')
    
    # Тестируем API
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get('/api/v1/logs/errors/test_service')
        assert response.status_code == 200
        errors = response.json()
        assert len(errors) > 0
        assert errors[0]['level'] == 'ERROR'
        assert errors[0]['error_message'] == 'Test error message'
        
        # Проверяем, что ошибка действительно сохранена
        result = await elastic_client.search(
            index='logs-test_service',
            body={
                'query': {
                    'bool': {
                        'must': [
                            {'term': {'level': 'ERROR'}},
                            {'match': {'error_message': 'Test error message'}}
                        ]
                    }
                }
            }
        )
        assert len(result['hits']['hits']) > 0 