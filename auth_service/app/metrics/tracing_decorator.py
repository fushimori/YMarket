import functools
import time
from opentelemetry import trace
from typing import Callable, Any
from fastapi import Request

def trace_function(name: str = None, include_request: bool = False):
    """
    Расширенный декоратор для трейсинга функций.
    
    Args:
        name: Имя для спана (если не указано, используется имя функции)
        include_request: Включать ли информацию о запросе в атрибуты спана
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = trace.get_tracer(__name__)
            span_name = name or func.__name__
            
            with tracer.start_as_current_span(span_name) as span:
                # Базовые атрибуты
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                # Добавляем информацию о запросе, если это FastAPI endpoint
                if include_request:
                    request = next((arg for arg in args if isinstance(arg, Request)), None)
                    if request:
                        span.set_attribute("http.method", request.method)
                        span.set_attribute("http.url", str(request.url))
                        span.set_attribute("http.host", request.headers.get("host", ""))
                        span.set_attribute("http.user_agent", request.headers.get("user-agent", ""))
                
                # Добавляем информацию о параметрах функции
                if kwargs:
                    # Фильтруем чувствительные данные
                    safe_kwargs = {k: v for k, v in kwargs.items() 
                                 if k not in ['password', 'token', 'secret']}
                    span.set_attribute("function.parameters", str(safe_kwargs))
                
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    duration = time.time() - start_time
                    
                    # Добавляем информацию о результате
                    span.set_attribute("function.duration_ms", duration * 1000)
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    
                    return result
                except Exception as e:
                    duration = time.time() - start_time
                    span.set_attribute("function.duration_ms", duration * 1000)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    raise
                
        return wrapper
    return decorator 