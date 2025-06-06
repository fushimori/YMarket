from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
from datetime import datetime, timedelta
from storage.elastic_client import ElasticClient
from http import HTTPStatus

router = APIRouter()

async def get_elastic_client():
    client = ElasticClient()
    await client.init()
    return client

@router.get("/logs/{service_name}")
async def get_logs(service_name: str, elastic_client: ElasticClient = Depends(get_elastic_client)):
    """Получение логов сервиса"""
    time_range = {
        'gte': (datetime.utcnow() - timedelta(hours=24)).isoformat(),
        'lte': datetime.utcnow().isoformat()
    }
    try:
        logs = await elastic_client.get_service_logs(service_name, time_range)
        return logs
    except Exception as e:
        print(f"Error getting service logs: {str(e)}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e))

@router.get("/logs/errors/{service_name}")
async def get_error_logs(service_name: str, elastic_client: ElasticClient = Depends(get_elastic_client)):
    """Получение ошибок сервиса"""
    time_range = {
        'gte': (datetime.utcnow() - timedelta(hours=24)).isoformat(),
        'lte': datetime.utcnow().isoformat()
    }
    try:
        logs = await elastic_client.get_service_logs(service_name, time_range, log_level="ERROR")
        return logs
    except Exception as e:
        print(f"Error getting error logs: {str(e)}")
        raise HTTPException(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=str(e)) 