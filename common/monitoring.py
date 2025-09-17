from prometheus_client import Counter, Histogram, Gauge
import time
from starlette.requests import Request
from starlette.responses import Response

# 请求计数器
REQUEST_COUNT = Counter(
    'api_request_count', 
    'Total number of API requests',
    ['method', 'endpoint', 'status_code']
)

# 请求处理时间直方图
REQUEST_LATENCY = Histogram(
    'api_request_latency_seconds', 
    'API request latency in seconds',
    ['method', 'endpoint']
)

# 数据库连接数监控
DB_CONNECTIONS = Gauge(
    'db_connections', 
    'Number of active database connections'
)

# 缓存命中率监控
CACHE_HIT_RATE = Gauge(
    'cache_hit_rate', 
    'Cache hit rate percentage'
)

# 错误计数器
ERROR_COUNT = Counter(
    'api_error_count', 
    'Number of API errors',
    ['method', 'endpoint', 'error_type']
)

# 事务计数器
TRANSACTION_COUNT = Counter(
    'transaction_count', 
    'Number of financial transactions',
    ['type', 'status']
)

# 基金净值计算指标
NET_VALUE_CALCULATION_TIME = Histogram(
    'net_value_calculation_time_seconds', 
    'Time taken to calculate fund net value'
)

# API网关请求分发指标
API_GATEWAY_REQUESTS = Counter(
    'api_gateway_requests', 
    'Requests passing through API gateway',
    ['service', 'status_code']
)

def track_request_metrics():
    """FastAPI中间件，用于跟踪请求指标"""
    async def middleware(request: Request, call_next):
        start_time = time.time()
        
        # 记录请求前的指标
        method = request.method
        endpoint = request.url.path
        
        # 处理请求
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # 记录错误
            ERROR_COUNT.labels(method=method, endpoint=endpoint, error_type=type(e).__name__).inc()
            raise
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 更新指标
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(process_time)
        
        return response
    
    return middleware

# 初始化监控系统
def init_monitoring():
    """初始化监控系统"""
    # 可以在这里添加更多初始化逻辑
    pass