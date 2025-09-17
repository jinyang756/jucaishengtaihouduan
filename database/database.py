from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 基础模型类
Base = declarative_base()

# Edge Config已被移除，使用环境变量和默认值

# 默认数据库连接配置
DEFAULT_DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": os.environ.get("DB_PORT", "3306"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "password"),
    "name": os.environ.get("DB_NAME", "green_ecology_fund")
}

# 获取数据库URL的函数
def get_database_url():
    """获取数据库连接URL，优先使用环境变量，否则使用默认值"""
    # 如果环境中直接提供了DATABASE_URL，则优先使用
    if os.environ.get("DATABASE_URL"):
        return os.environ.get("DATABASE_URL")
    
    # 使用默认配置
    return f"mariadb+mariadbconnector://{DEFAULT_DB_CONFIG['user']}:{DEFAULT_DB_CONFIG['password']}@{DEFAULT_DB_CONFIG['host']}:{DEFAULT_DB_CONFIG['port']}/{DEFAULT_DB_CONFIG['name']}?charset=utf8mb4"

# 创建数据库引擎
# 增加连接池配置，提高连接稳定性
database_url = get_database_url()
engine = create_engine(
    database_url,
    pool_pre_ping=True,           # 连接前检查有效性
    pool_recycle=300,             # 连接回收时间（秒）
    pool_size=10,                 # 连接池大小
    max_overflow=20,              # 最大额外连接数
    pool_timeout=30,              # 连接等待超时（秒）
    echo=False,                   # 禁用SQL语句日志输出
    connect_args={
        'connect_timeout': 10,    # 连接超时（秒）
        'read_timeout': 30,       # 读取超时（秒）
        'write_timeout': 30       # 写入超时（秒）
    }
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """创建数据库表"""
    Base.metadata.create_all(bind=engine)

# 提供异步版本的数据库会话获取函数
async def get_db_async():
    """异步获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()