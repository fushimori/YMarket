import json
import functools
import asyncio
from aiokafka import AIOKafkaProducer
from datetime import datetime

# Kafka configuration
KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
# KAFKA_TOPIC = "catalog_logs"

async def get_kafka_producer():
    try:
        producer = AIOKafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await producer.start()
        return producer
    except Exception as e:
        print(f"Error creating Kafka producer: {e}")
        raise

def log_to_kafka(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = datetime.now()
        try:
            # Get request object from args if it exists
            request = next((arg for arg in args if hasattr(arg, 'json')), None)
            
            # Prepare log data
            log_data = {
                "timestamp": start_time.isoformat(),
                "service": "catalog_service",
                "endpoint": func.__name__,
                "status": "started",
                "request_data": {}
            }
            
            # Try to get request data if available
            if request:
                try:
                    log_data["request_data"] = await request.json()
                except:
                    pass
            
            # Execute the original function
            result = await func(*args, **kwargs)
            
            # Update log data with success
            log_data.update({
                "status": "success",
                "duration_ms": (datetime.now() - start_time).total_seconds() * 1000
            })
            
            # Send log to Kafka
            producer = await get_kafka_producer()
            print("LOG_TO_KAFKA: sending log", log_data)
            await producer.send_and_wait("logs", log_data)
            await producer.stop()
            
            return result
            
        except Exception as e:
            # Update log data with error
            log_data.update({
                "status": "error",
                "error": str(e),
                "duration_ms": (datetime.now() - start_time).total_seconds() * 1000
            })
            
            # Send error log to Kafka
            producer = await get_kafka_producer()
            print("LOG_TO_KAFKA: sending error", log_data)
            await producer.send_and_wait("errors", log_data)
            await producer.stop()
            
            raise
    
    return wrapper 