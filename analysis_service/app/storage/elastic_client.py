from elasticsearch import AsyncElasticsearch
from typing import Dict, Any, List
from config.settings import settings

class ElasticClient:
    def __init__(self):
        self.es = None
        
    async def init(self):
        """Initialize Elasticsearch client"""
        if self.es is None:
            self.es = AsyncElasticsearch(
                [f"http://{settings.ELASTICSEARCH_HOST}:{settings.ELASTICSEARCH_PORT}"],
                basic_auth=(
                    settings.ELASTICSEARCH_USERNAME,
                    settings.ELASTICSEARCH_PASSWORD
                ) if settings.ELASTICSEARCH_USERNAME else None
            )
        return self
        
    async def close(self):
        """Close Elasticsearch client"""
        if self.es is not None:
            await self.es.close()
            self.es = None
            
    async def index_log(self, log_data: Dict[str, Any]) -> bool:
        """
        Индексирование лога в Elasticsearch
        
        Args:
            log_data: Данные лога для индексирования
            
        Returns:
            bool: Успешность операции
        """
        try:
            if self.es is None:
                await self.init()
            response = await self.es.index(
                index=f"logs-{log_data['service']}",
                document=log_data
            )
            return response['result'] == 'created'
        except Exception as e:
            print(f"Error indexing log: {str(e)}")
            return False
            
    async def search_logs(self,
                   service_name: str,
                   query: Dict[str, Any],
                   size: int = 100) -> List[Dict[str, Any]]:
        """
        Поиск логов в Elasticsearch
        
        Args:
            service_name: Имя сервиса
            query: Поисковый запрос
            size: Количество результатов
            
        Returns:
            List[Dict[str, Any]]: Список найденных логов
        """
        try:
            if self.es is None:
                await self.init()
                
            response = await self.es.search(
                index=f"logs-{service_name}",
                body={
                    "query": query,
                    "size": size,
                    "sort": [{"timestamp": "desc"}]
                }
            )
            return [hit['_source'] for hit in response['hits']['hits']]
        except Exception as e:
            print(f"Error searching logs: {str(e)}")
            return []
            
    async def get_service_logs(self,
                        service_name: str,
                        time_range: Dict[str, str],
                        log_level: str = None) -> List[Dict[str, Any]]:
        """
        Получение логов сервиса за определенный период
        
        Args:
            service_name: Имя сервиса
            time_range: Временной диапазон
            log_level: Уровень лога (опционально)
            
        Returns:
            List[Dict[str, Any]]: Список логов
        """
        must_conditions = [
            {"range": {"timestamp": time_range}}
        ]
        
        if log_level:
            must_conditions.append({"term": {"level": log_level}})
            
        query = {
            "bool": {
                "must": must_conditions
            }
        }
        
        try:
            if self.es is None:
                await self.init()
                
            response = await self.es.search(
                index=f"logs-{service_name}",
                body={
                    "query": query,
                    "size": 100,
                    "sort": [{"timestamp": "desc"}]
                }
            )
            return [hit['_source'] for hit in response['hits']['hits']]
        except Exception as e:
            print(f"Error getting service logs: {str(e)}")
            return [] 