from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest
import time

# Create registry
registry = CollectorRegistry()

# ====== HTTP REQUEST METRICS ======
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=registry
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
    registry=registry
)

# ====== ERROR METRICS ======
http_requests_errors_total = Counter(
    'http_requests_errors_total',
    'Total HTTP request errors',
    ['method', 'endpoint', 'error_type'],
    registry=registry
)

# ====== AUTHENTICATION METRICS ======
auth_attempts_total = Counter(
    'auth_attempts_total',
    'Total authentication attempts',
    ['broker', 'status'],
    registry=registry
)

auth_duration_seconds = Histogram(
    'auth_duration_seconds',
    'Authentication latency',
    ['broker'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry
)

# ====== TRADE METRICS ======
trades_placed_total = Counter(
    'trades_placed_total',
    'Total trades placed',
    ['trade_type', 'broker', 'status'],
    registry=registry
)

trade_execution_duration_seconds = Histogram(
    'trade_execution_duration_seconds',
    'Trade execution latency',
    ['broker'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=registry
)

# ====== PORTFOLIO METRICS ======
portfolio_updates_total = Counter(
    'portfolio_updates_total',
    'Portfolio update events',
    ['operation', 'status'],
    registry=registry
)

portfolio_value_usd = Gauge(
    'portfolio_value_usd',
    'Current portfolio value in USD',
    ['user_id', 'broker'],
    registry=registry
)

# ====== QUEUE METRICS ======
redis_queue_depth = Gauge(
    'redis_queue_depth',
    'Current queue depth in Redis',
    ['queue_name'],
    registry=registry
)

task_retry_count = Counter(
    'task_retry_count',
    'Task retry count',
    ['task_name', 'status'],
    registry=registry
)

dlq_message_count = Counter(
    'dlq_message_count',
    'Dead letter queue messages',
    ['queue_name'],
    registry=registry
)

# ====== BROKER API METRICS ======
broker_api_calls_total = Counter(
    'broker_api_calls_total',
    'Total broker API calls',
    ['broker', 'endpoint', 'status'],
    registry=registry
)

broker_api_duration_seconds = Histogram(
    'broker_api_duration_seconds',
    'Broker API latency',
    ['broker', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=registry
)

# ====== CACHE METRICS ======
cache_hits_total = Counter(
    'cache_hits_total',
    'Cache hits',
    ['cache_name'],
    registry=registry
)

cache_misses_total = Counter(
    'cache_misses_total',
    'Cache misses',
    ['cache_name'],
    registry=registry
)

cache_size_bytes = Gauge(
    'cache_size_bytes',
    'Cache size in bytes',
    ['cache_name'],
    registry=registry
)

# ====== DATABASE METRICS ======
mongodb_query_duration_seconds = Histogram(
    'mongodb_query_duration_seconds',
    'MongoDB query latency',
    ['operation', 'collection'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0],
    registry=registry
)

mongodb_operations_total = Counter(
    'mongodb_operations_total',
    'MongoDB operations',
    ['operation', 'collection', 'status'],
    registry=registry
)

# ====== AI/LLM METRICS ======
gemini_api_calls_total = Counter(
    'gemini_api_calls_total',
    'Gemini API calls',
    ['status'],
    registry=registry
)

gemini_api_duration_seconds = Histogram(
    'gemini_api_duration_seconds',
    'Gemini API latency',
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0],
    registry=registry
)

gemini_tokens_used = Counter(
    'gemini_tokens_used',
    'Gemini tokens consumed',
    ['type'],
    registry=registry
)

# ====== MARKET DATA METRICS ======
market_data_fetch_duration_seconds = Histogram(
    'market_data_fetch_duration_seconds',
    'Market data fetch latency',
    ['source'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0],
    registry=registry
)

market_data_updates_total = Counter(
    'market_data_updates_total',
    'Market data updates',
    ['source', 'status'],
    registry=registry
)


# ====== HELPER FUNCTIONS ======
def track_time(metric_histogram: Histogram, metric_counter: Counter = None, **labels):
    """Decorator to track execution time"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                metric_histogram.labels(**labels).observe(duration)
                if metric_counter:
                    metric_counter.labels(**labels, status="success").inc()
        
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                metric_histogram.labels(**labels).observe(duration)
                if metric_counter:
                    metric_counter.labels(**labels, status="success").inc()
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator