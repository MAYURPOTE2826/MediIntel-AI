from prometheus_client import Gauge, Histogram, Counter

# 1. API response times (handled by prometheus-flask-exporter automatically)
# 2. OCR accuracy rate (%)
ocr_accuracy_gauge = Gauge(
    'medintel_ocr_accuracy_rate',
    'Accuracy rate of the OCR processing (%)',
    ['module']
)

# 3. AI confidence distribution
ai_confidence_histogram = Histogram(
    'medintel_ai_confidence',
    'Confidence score of AI models',
    ['model_name'],
    buckets=[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 1.0]
)

# 4. User upload volume
upload_volume_counter = Counter(
    'medintel_upload_volume_total',
    'Total volume of files uploaded in bytes',
    ['file_type']
)

# 5. Error rates by module (Mostly handled by flask exporter, but we can track specific ones)
module_error_counter = Counter(
    'medintel_module_errors_total',
    'Total number of errors per module',
    ['module', 'error_type']
)

# 6. Database query performance
db_query_latency_histogram = Histogram(
    'medintel_db_query_duration_seconds',
    'Database query latency in seconds',
    ['query_type'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
)

# 7. AI model inference time
ai_inference_latency_histogram = Histogram(
    'medintel_ai_inference_duration_seconds',
    'AI model inference latency in seconds',
    ['model_name'],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)
