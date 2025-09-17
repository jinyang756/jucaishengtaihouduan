import uvicorn
import logging
import os
from service import app
from database.database import create_tables
import uvicorn

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("user_service")

# 创建表结构
def init_db():
    """初始化数据库，创建表结构"""
    try:
        create_tables()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

# 启动服务
if __name__ == "__main__":
    # 初始化数据库
    init_db()
    
    # 从环境变量获取端口和主机配置
    port = int(os.environ.get("PORT", 8004))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = os.environ.get("RELOAD", "True").lower() == "true"
    
    logger.info(f"Starting User Service on {host}:{port}")
    uvicorn.run("service:app", host=host, port=port, reload=reload)