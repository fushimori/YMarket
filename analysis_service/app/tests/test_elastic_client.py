import pytest
from datetime import datetime, timedelta
from storage.elastic_client import ElasticClient
from storage.index_manager import IndexManager

@pytest.mark.asyncio
async def test_index_log(elastic_client):
    # Создаем тестовый лог
    test_log = {
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'test_service',
        'level': 'INFO',
        'message': 'Test log message',
        'metadata': {'test': 'data'}
    }
    
    # Индексируем лог
    await elastic_client.index(
        index='logs-test_service',
        document=test_log
    )
    await elastic_client.indices.refresh(index='logs-test_service')
    
    # Проверяем, что лог сохранен
    result = await elastic_client.search(
        index='logs-test_service',
        body={
            'query': {
                'match': {
                    'message': 'Test log message'
                }
            }
        }
    )
    
    assert len(result['hits']['hits']) > 0
    saved_log = result['hits']['hits'][0]['_source']
    assert saved_log['message'] == 'Test log message'

@pytest.mark.asyncio
async def test_search_logs(elastic_client):
    # Создаем тестовые логи
    test_logs = [
        {
            'timestamp': (datetime.utcnow() - timedelta(hours=1)).isoformat(),
            'service': 'test_service',
            'level': 'INFO',
            'message': 'Test log 1',
            'metadata': {'test': 'data1'}
        },
        {
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'test_service',
            'level': 'ERROR',
            'message': 'Test log 2',
            'metadata': {'test': 'data2'}
        }
    ]
    
    # Индексируем логи
    for log in test_logs:
        await elastic_client.index(
            index='logs-test_service',
            document=log
        )
    
    await elastic_client.indices.refresh(index='logs-test_service')
    
    # Тестируем поиск по времени
    time_range = {
        'gte': (datetime.utcnow() - timedelta(hours=2)).isoformat(),
        'lte': datetime.utcnow().isoformat()
    }
    
    result = await elastic_client.search(
        index='logs-test_service',
        body={
            'query': {
                'bool': {
                    'must': [
                        {'range': {'timestamp': time_range}}
                    ]
                }
            }
        }
    )
    logs = [hit['_source'] for hit in result['hits']['hits']]
    assert len(logs) == 2
    
    # Тестируем поиск по уровню
    result = await elastic_client.search(
        index='logs-test_service',
        body={
            'query': {
                'bool': {
                    'must': [
                        {'range': {'timestamp': time_range}},
                        {'term': {'level': 'ERROR'}}
                    ]
                }
            }
        }
    )
    logs = [hit['_source'] for hit in result['hits']['hits']]
    assert len(logs) == 1
    assert logs[0]['level'] == 'ERROR'

@pytest.mark.asyncio
async def test_index_lifecycle(elastic_client):
    # Создаем тестовые логи с разными датами
    test_logs = [
        {
            'timestamp': (datetime.utcnow() - timedelta(days=31)).isoformat(),
            'service': 'test_service',
            'level': 'INFO',
            'message': 'Old log',
            'metadata': {'test': 'old'}
        },
        {
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'test_service',
            'level': 'INFO',
            'message': 'New log',
            'metadata': {'test': 'new'}
        }
    ]
    
    # Индексируем логи
    for log in test_logs:
        await elastic_client.index(
            index='logs-test_service',
            document=log
        )
    
    await elastic_client.indices.refresh(index='logs-test_service')
    
    # Запускаем очистку старых индексов
    index_manager = IndexManager()
    await index_manager.cleanup_old_indices(days=30)
    await elastic_client.indices.refresh(index='logs-test_service')
    
    # Проверяем, что старые логи удалены
    result = await elastic_client.search(
        index='logs-test_service',
        body={
            'query': {
                'bool': {
                    'must': [
                        {'match': {'message': 'Old log'}},
                        {'range': {
                            'timestamp': {
                                'lte': (datetime.utcnow() - timedelta(days=30)).isoformat()
                            }
                        }}
                    ]
                }
            }
        }
    )
    
    assert len(result['hits']['hits']) == 0
    
    # Проверяем, что новые логи сохранены
    result = await elastic_client.search(
        index='logs-test_service',
        body={
            'query': {
                'match': {
                    'message': 'New log'
                }
            }
        }
    )
    
    assert len(result['hits']['hits']) > 0 