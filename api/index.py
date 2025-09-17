from fastapi import FastAPI, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from datetime import datetime
import httpx
import os
from .vercel_edge_config import EdgeConfig

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
    os.environ.get("FRONTEND_URL", "https://your-frontend.vercel.app")
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 在Serverless环境中，微服务通过直接导入方式集成
# 所以这里不需要配置微服务URL

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
@app.get("/api/health")
async def health_check():
    """API网关健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

# 简单的基金数据接口，用于测试
@app.get("/api/funds")
async def get_funds():
    # 在实际部署中，这里应该连接数据库获取真实数据
    return {"funds": [], "message": "Serverless API is working"}

# Welcome路由 - 使用Edge Config获取问候语
@app.get("/welcome")
async def get_welcome_message():
    """从Edge Config获取问候语配置并返回"""
    try:
        # 初始化EdgeConfig客户端
        edge_config = EdgeConfig()
        
        # 从Edge Config获取问候语配置
        greeting = await edge_config.get("greeting")
        
        # 如果配置存在，返回配置的问候语；否则返回默认问候语
        if greeting:
            return JSONResponse(content=greeting)
        else:
            return JSONResponse(content={"message": "Welcome to the Green Ecology Fund API!"})
    except Exception as e:
        logger.error(f"Error retrieving greeting from Edge Config: {e}")
        return JSONResponse(
            content={"error": "Failed to retrieve greeting", "details": str(e)},
            status_code=500
        )

# WebSocket连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

# 创建WebSocket管理器实例
manager = ConnectionManager()

# WebSocket端点
@app.websocket("/api/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    # 接受连接
    await manager.connect(websocket)
    try:
        # 发送欢迎消息
        await websocket.send_text(f"Welcome client {client_id}!")
        # 广播新客户端加入
        await manager.broadcast(f"Client {client_id} joined the chat")
        
        # 持续接收消息
        while True:
            data = await websocket.receive_text()
            # 广播接收到的消息
            await manager.broadcast(f"Client {client_id} says: {data}")
    except WebSocketDisconnect:
        # 客户端断开连接时处理
        manager.disconnect(websocket)
        await manager.broadcast(f"Client {client_id} left the chat")
    except Exception as e:
        # 处理其他异常
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# 处理Vercel的Serverless函数要求
def handler(event, context):
    from mangum import Mangum
    
    asgi_handler = Mangum(app)
    return asgi_handler(event, context)

# 开发环境下直接运行
if __name__ == "__main__":
    import uvicorn
    # 从环境变量获取端口和主机配置
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    
    logger.info(f"Starting API Gateway on {host}:{port}")
    uvicorn.run("index:app", host=host, port=port, reload=True)