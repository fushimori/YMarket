from typing import Dict, Any
from datetime import datetime
from storage.elastic_client import ElasticClient

class LogProcessor:
    def __init__(self):
        self.elastic_client = ElasticClient()

    async def process_log(self, log_data: Dict[str, Any], is_error: bool = False) -> bool:
        """
        Обработка и сохранение лога
        
        Args:
            log_data: Данные лога из Kafka
            is_error: Флаг, указывающий что это лог ошибки
            
        Returns:
            bool: Успешность обработки
        """
        try:
            # Добавляем время обработки и тип лога
            log_data['processed_at'] = datetime.utcnow().isoformat()
            log_data['log_type'] = 'error' if is_error else 'log'
            
            # Сохраняем в Elasticsearch
            return await self.elastic_client.index_log(log_data)
        except Exception as e:
            print(f"Error processing {'error' if is_error else 'log'}: {str(e)}")
            return False

    async def process_error(self, error_data: Dict[str, Any]) -> bool:
        """
        Обработка и сохранение ошибки
        
        Args:
            error_data: Данные об ошибке из Kafka
            
        Returns:
            bool: Успешность обработки
        """
        try:
            # Добавляем время обработки
            error_data['processed_at'] = datetime.utcnow().isoformat()
            
            # Сохраняем в Elasticsearch
            return await self.elastic_client.index_log(error_data)
        except Exception as e:
            print(f"Error processing error log: {str(e)}")
            return False 