from prometheus_client import Counter, Histogram, generate_latest
from fastapi import Response
from typing import Dict, Any
import time
from functools import wraps

class BaseMetrics:
    """Базовый класс для метрик, который можно использовать во всех сервисах"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.metrics: Dict[str, Any] = {}
        self._setup_metrics()

    def _setup_metrics(self):
        """Базовая настройка метрик"""
        # Метрики для API
        self.metrics['api_requests'] = Counter(
            'api_requests_total',
            'Total number of API requests',
            ['service', 'endpoint', 'method', 'status']
        )

        self.metrics['api_duration'] = Histogram(
            'api_request_duration_seconds',
            'Time spent processing API requests',
            ['service', 'endpoint', 'method']
        )

        # Метрики для базы данных
        self.metrics['db_operations'] = Counter(
            'db_operations_total',
            'Total number of database operations',
            ['service', 'operation', 'status']
        )

        self.metrics['db_duration'] = Histogram(
            'db_operation_duration_seconds',
            'Time spent on database operations',
            ['service', 'operation']
        )

    def api_metrics(self):
        """Декоратор для автоматического сбора метрик API"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    response = await func(*args, **kwargs)
                    status = 'success'
                except Exception as e:
                    status = 'error'
                    raise e
                finally:
                    duration = time.time() - start_time
                    self.metrics['api_requests'].labels(
                        service=self.service_name,
                        endpoint=func.__name__,
                        method='GET',  # TODO: сделать динамическим
                        status=status
                    ).inc()
                    
                    self.metrics['api_duration'].labels(
                        service=self.service_name,
                        endpoint=func.__name__,
                        method='GET'  # TODO: сделать динамическим
                    ).observe(duration)
                return response
            return wrapper
        return decorator

    def db_metrics(self, operation: str):
        """Декоратор для автоматического сбора метрик БД"""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    status = 'success'
                except Exception as e:
                    status = 'error'
                    raise e
                finally:
                    duration = time.time() - start_time
                    self.metrics['db_operations'].labels(
                        service=self.service_name,
                        operation=operation,
                        status=status
                    ).inc()
                    
                    self.metrics['db_duration'].labels(
                        service=self.service_name,
                        operation=operation
                    ).observe(duration)
                return result
            return wrapper
        return decorator

    async def metrics_endpoint(self):
        """Эндпоинт для Prometheus"""
        return Response(generate_latest(), media_type='text/plain')