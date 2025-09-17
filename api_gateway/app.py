from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import time
from datetime import datetime
import httpx
import os

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("api_gateway")

# 创建FastAPI应用
app = FastAPI(
    title="聚财生态基金API网关",
    description="绿色生态基金虚拟净值模拟系统的API网关",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
    "https://your-frontend-domain.com"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 微服务URL配置
SERVICES = {
    "rule_service": os.environ.get("RULE_SERVICE_URL", "http://localhost:8000"),
    "news_service": os.environ.get("NEWS_SERVICE_URL", "http://localhost:8001"),
    "calculation_service": os.environ.get("CALCULATION_SERVICE_URL", "http://localhost:8002"),
    "fund_service": os.environ.get("FUND_SERVICE_URL", "http://localhost:8003"),
    "user_service": os.environ.get("USER_SERVICE_URL", "http://localhost:8004")
}

# 请求/响应日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求和响应日志"""
    start_time = time.time()
    logger.info(f"Request: {request.method} {request.url}")
    
    # 获取请求体
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.body()
            if body:
                logger.debug(f"Request body: {body.decode('utf-8')}")
        except Exception as e:
            logger.error(f"Error reading request body: {e}")
    
    # 处理请求
    response = await call_next(request)
    
    # 计算处理时间
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.4f}s")
    
    return response

# 健康检查接口
@app.get("/health")
def health_check():
    """API网关健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# 服务状态检查接口
@app.get("/services/health")
async def services_health_check():
    """检查所有微服务的健康状态"""
    results = {}
    
    async with httpx.AsyncClient() as client:
        for service_name, service_url in SERVICES.items():
            try:
                # 尝试调用每个服务的健康检查接口
                response = await client.get(f"{service_url}/health", timeout=5.0)
                if response.status_code == 200:
                    results[service_name] = {
                        "status": "healthy",
                        "url": service_url
                    }
                else:
                    results[service_name] = {
                        "status": "unhealthy",
                        "url": service_url,
                        "code": response.status_code
                    }
            except Exception as e:
                results[service_name] = {
                    "status": "error",
                    "url": service_url,
                    "error": str(e)
                }
    
    return results

# 服务发现接口
@app.get("/services")
def list_services():
    """列出所有可用的微服务"""
    return {
        "services": SERVICES,
        "total": len(SERVICES)
    }

# 代理请求到各个微服务
@app.api_route("/api/rule_service/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_rule_service(request: Request, path: str):
    """代理请求到规则服务"""
    return await proxy_request(request, "rule_service", path)

@app.api_route("/api/news_service/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_news_service(request: Request, path: str):
    """代理请求到新闻服务"""
    return await proxy_request(request, "news_service", path)

@app.api_route("/api/calculation_service/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_calculation_service(request: Request, path: str):
    """代理请求到计算服务"""
    return await proxy_request(request, "calculation_service", path)

@app.api_route("/api/fund_service/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_fund_service(request: Request, path: str):
    """代理请求到基金服务"""
    return await proxy_request(request, "fund_service", path)

@app.api_route("/api/user_service/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_to_user_service(request: Request, path: str):
    """代理请求到用户服务"""
    return await proxy_request(request, "user_service", path)

# 代理请求的核心实现
async def proxy_request(request: Request, service_name: str, path: str):
    """将请求代理到指定的微服务"""
    if service_name not in SERVICES:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Service '{service_name}' not found"}
        )
    
    service_url = SERVICES[service_name]
    target_url = f"{service_url}/{path}"
    
    # 复制请求头
    headers = dict(request.headers)
    # 移除可能导致问题的头
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    # 读取请求体
    body = await request.body()
    
    try:
        async with httpx.AsyncClient() as client:
            # 发送请求到目标服务
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                timeout=30.0  # 设置超时时间
            )
            
            # 创建响应
            proxy_response = Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
            return proxy_response
    except httpx.RequestError as e:
        logger.error(f"Error proxying to {service_name}: {e}")
        return JSONResponse(
            status_code=503,
            content={"detail": f"Service '{service_name}' unavailable: {str(e)}"}
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

# 启动服务
if __name__ == "__main__":
    # 从环境变量获取端口和主机配置
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting API Gateway on {host}:{port}")
    uvicorn.run("app:app", host=host, port=port, reload=True)