from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import asyncio

# 基础模型类
Base = declarative_base()

# 尝试导入项目中自定义的Edge Config模块
edge_config_available = False
edge_config_client = None
try:
    # 尝试从项目中导入自定义的EdgeConfig类
    from api.vercel_edge_config import EdgeConfig
    edge_config_available = True
    edge_config_client = EdgeConfig()
except ImportError:
    # 如果无法导入自定义的EdgeConfig，使用环境变量或默认值
    pass

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
    """获取数据库连接URL，优先从Edge Config获取，如果不可用则使用环境变量或默认值"""
    if edge_config_available:
        try:
            # 在同步环境中使用asyncio.run调用异步函数
            db_config = asyncio.run(get_db_config_from_edge())
            return f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['name']}"
        except Exception as e:
            print(f"Failed to get DB config from Edge Config: {e}")
            # 出错时回退到默认配置
    
    # 如果环境中直接提供了DATABASE_URL，则优先使用
    if os.environ.get("DATABASE_URL"):
        return os.environ.get("DATABASE_URL")
    
    # 使用默认配置
    return f"mysql+pymysql://{DEFAULT_DB_CONFIG['user']}:{DEFAULT_DB_CONFIG['password']}@{DEFAULT_DB_CONFIG['host']}:{DEFAULT_DB_CONFIG['port']}/{DEFAULT_DB_CONFIG['name']}"

# 异步函数：从Edge Config获取数据库配置
async def get_db_config_from_edge():
    """从Vercel Edge Config异步获取数据库配置"""
    try:
        global edge_config_client
        if edge_config_client is None:
            edge_config_client = EdgeConfig()
            
        # 使用项目中自定义的EdgeConfig类获取配置
        db_config = {
            "host": (await edge_config_client.get('DB_HOST')) or DEFAULT_DB_CONFIG['host'],
            "port": (await edge_config_client.get('DB_PORT')) or DEFAULT_DB_CONFIG['port'],
            "user": (await edge_config_client.get('DB_USER')) or DEFAULT_DB_CONFIG['user'],
            "password": (await edge_config_client.get('DB_PASSWORD')) or DEFAULT_DB_CONFIG['password'],
            "name": (await edge_config_client.get('DB_NAME')) or DEFAULT_DB_CONFIG['name']
        }
        return db_config
    except Exception as e:
        print(f"Error getting DB config from Edge Config: {e}")
        return DEFAULT_DB_CONFIG

# 创建数据库引擎
database_url = get_database_url()
engine = create_engine(database_url, pool_pre_ping=True, pool_recycle=300)

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