from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum
import os
from dotenv import load_dotenv
import logging

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("vercel_api")

# 创建FastAPI应用
app = FastAPI(
    title="聚财生态基金系统",
    description="绿色生态基金虚拟净值模拟系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
origins = [
    "*",  # 生产环境应替换为具体的前端URL
    os.environ.get("FRONTEND_URL", ""),
    "http://localhost:3000",
    "http://localhost:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 根路径端点
@app.get("/")
def root():
    """根路径，返回系统信息"""
    return {
        "app": "聚财生态基金系统API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

# 健康检查端点
@app.get("/health")
def health_check():
    """健康检查端点"""
    try:
        # 简单检查环境变量是否加载
        db_name = os.environ.get("DB_NAME", "未配置")
        return {
            "status": "healthy",
            "environment": os.environ.get("VERCEL_ENV", "development"),
            "database": db_name,
            "message": "系统运行正常"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Edge Config测试端点
@app.get("/welcome")
def welcome():
    """测试Edge Config集成"""
    try:
        # 尝试获取Edge Config值
        welcome_message = os.environ.get("WELCOME_MESSAGE", "欢迎使用聚财生态基金系统")
        return {
            "message": welcome_message,
            "source": "environment variable"
        }
    except Exception as e:
        logger.error(f"Welcome endpoint error: {str(e)}")
        return {
            "message": "欢迎使用聚财生态基金系统",
            "source": "fallback",
            "error": str(e)
        }

# 导出为Vercel Serverless Function
handler = Mangum(app)

# 本地开发环境运行时的配置
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = os.environ.get("RELOAD", "True").lower() == "true"
    logger.info(f"Starting API on {host}:{port}")
    uvicorn.run("index:app", host=host, port=port, reload=reload)