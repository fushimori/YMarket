import pytest
from datetime import datetime
from consumers.kafka_consumer import KafkaLogConsumer
from processors.log_processor import LogProcessor

@pytest.mark.asyncio
async def test_process_log(kafka_producer, elastic_client):
    # Создаем тестовый лог
    test_log = {
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'test_service',
        'level': 'INFO',
        'message': 'Test log message',
        'metadata': {'test': 'data'}
    }
    
    # Отправляем лог в Kafka
    await kafka_producer.send_and_wait(
        topic='logs',
        value=test_log
    )
    
    # Инициализируем consumer и processor
    consumer = KafkaLogConsumer()
    processor = LogProcessor()
    
    # Обрабатываем лог
    success = await processor.process_log(test_log)
    assert success is True
    
    # Проверяем, что лог сохранен в Elasticsearch
    await elastic_client.indices.refresh(index='logs-test_service')
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
    assert 'processed_at' in saved_log

@pytest.mark.asyncio
async def test_process_error(kafka_producer, elastic_client):
    # Создаем тестовую ошибку
    test_error = {
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'test_service',
        'level': 'ERROR',
        'error_type': 'TestError',
        'error_message': 'Test error message',
        'stack_trace': 'Test stack trace',
        'metadata': {'test': 'data'}
    }
    
    # Отправляем ошибку в Kafka
    await kafka_producer.send_and_wait(
        topic='errors',
        value=test_error
    )
    
    # Инициализируем consumer и processor
    consumer = KafkaLogConsumer()
    processor = LogProcessor()
    
    # Обрабатываем ошибку
    success = await processor.process_error(test_error)
    assert success is True
    
    # Проверяем, что ошибка сохранена в Elasticsearch
    await elastic_client.indices.refresh(index='logs-test_service')
    result = await elastic_client.search(
        index='logs-test_service',
        body={
            'query': {
                'match': {
                    'error_message': 'Test error message'
                }
            }
        }
    )
    
    assert len(result['hits']['hits']) > 0
    saved_error = result['hits']['hits'][0]['_source']
    assert saved_error['error_message'] == 'Test error message'
    assert saved_error['level'] == 'ERROR'
    assert 'processed_at' in saved_error 