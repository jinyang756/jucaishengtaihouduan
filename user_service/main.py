import uvicorn
import logging
import os
from database.database import create_tables

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

# 初始化数据库（如果直接运行此文件）
if __name__ == "__main__":
    init_db()