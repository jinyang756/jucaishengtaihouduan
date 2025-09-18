from fastapi import FastAPI
import uvicorn
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
logger = logging.getLogger("main_app")

# 创建FastAPI应用作为主入口点
app = FastAPI(
    title="聚财生态基金系统",
    description="绿色生态基金虚拟净值模拟系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 根路径端点
@app.get("/")
def root():
    """根路径，返回系统信息"""
    return {
        "app": "聚财生态基金系统",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

# 健康检查端点
@app.get("/health")
def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "environment": os.environ.get("VERCEL_ENV", "development")
    }

# 在开发环境中运行时的配置
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = os.environ.get("RELOAD", "True").lower() == "true"
    
    logger.info(f"Starting Main Application on {host}:{port}")
    uvicorn.run("app:app", host=host, port=port, reload=reload)