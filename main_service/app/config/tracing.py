from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3Format
from fastapi import FastAPI

def setup_tracing(app: FastAPI, service_name: str = "main_service"):
    """
    Настройка трейсинга для сервиса с использованием Jaeger.
    """
    # Создаем ресурс с информацией о сервисе
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
        "deployment.environment": "development"
    })

    # Настраиваем провайдер трейсинга с ALWAYS_ON сэмплингом
    tracer_provider = TracerProvider(
        resource=resource,
        sampler=ALWAYS_ON
    )
    trace.set_tracer_provider(tracer_provider)

    # Настраиваем экспортер для Jaeger
    otlp_exporter = OTLPSpanExporter(
        endpoint="jaeger:4317",
        insecure=True
    )
    
    # Добавляем процессор для отправки трейсов в Jaeger
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    # Устанавливаем глобальный пропагатор для контекста
    set_global_textmap(B3Format())

    # Инструментируем FastAPI приложение
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=tracer_provider,
        excluded_urls="health,metrics"  # Исключаем health check и metrics эндпоинты
    )

    # Инструментируем HTTP клиент для автоматической пропагации контекста
    HTTPXClientInstrumentor().instrument()

    return trace.get_tracer(__name__) 