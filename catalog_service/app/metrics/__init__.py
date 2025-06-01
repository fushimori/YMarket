from .base_metrics import BaseMetrics

# Create a default instance for the catalog service
metrics = BaseMetrics('catalog_service')

# Export the required functions
metrics_endpoint = metrics.metrics_endpoint
db_metrics = metrics.db_metrics
api_metrics = metrics.api_metrics

__all__ = ['BaseMetrics', 'metrics_endpoint', 'api_metrics', 'db_metrics'] 