from .base_metrics import BaseMetrics

# Create a default instance for the analysis service
metrics = BaseMetrics('analysis_service')

# Export the required functions
metrics_endpoint = metrics.metrics_endpoint
api_metrics = metrics.api_metrics
db_metrics = metrics.db_metrics

__all__ = ['BaseMetrics', 'metrics_endpoint', 'api_metrics', 'db_metrics'] 