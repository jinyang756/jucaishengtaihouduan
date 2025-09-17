import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# Edge Config配置 - 用于Vercel边缘环境
# 注意：在非Vercel环境中，仍会使用环境变量作为备选
class EdgeConfig:
    # Vercel Edge Config 配置
    EDGE_CONFIG_ID = os.environ.get("EDGE_CONFIG_ID", "ecfg_xfrfdjmkzodtkhqy4c8jhs0loyed")
    EDGE_CONFIG_TOKEN = os.environ.get("EDGE_CONFIG_TOKEN", "d5ba143a-2429-433b-a2cb-7f75161bd918")
    EDGE_CONFIG_DIGEST = os.environ.get("EDGE_CONFIG_DIGEST", "5bf6b008a9ec05f6870c476d10b53211797aa000f95aae344ae60f9b422286da")

# 数据库配置
class DatabaseConfig:
    # 在实际运行时，会通过Edge Config动态获取这些值
    # 这里提供默认值仅作为开发环境备用
    HOST = os.environ.get("DB_HOST", "localhost")
    PORT = int(os.environ.get("DB_PORT", "3306"))
    USER = os.environ.get("DB_USER", "root")
    PASSWORD = os.environ.get("DB_PASSWORD", "password")
    NAME = os.environ.get("DB_NAME", "green_ecology_fund")
    
    @property
    def URL(self):
        return f"mysql+mysqlconnector://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"

# 异步获取Edge Config中的数据库配置
try:
    from edge_config import get as get_edge_config
    
    async def get_db_config_from_edge():
        """从Vercel Edge Config异步获取数据库配置"""
        try:
            # 从Edge Config获取数据库配置
            db_host = await get_edge_config('DB_HOST') or config.db.HOST
            db_port = await get_edge_config('DB_PORT') or config.db.PORT
            db_user = await get_edge_config('DB_USER') or config.db.USER
            db_password = await get_edge_config('DB_PASSWORD') or config.db.PASSWORD
            db_name = await get_edge_config('DB_NAME') or config.db.NAME
            
            # 创建新的数据库配置对象
            class EdgeDatabaseConfig:
                HOST = db_host
                PORT = int(db_port)
                USER = db_user
                PASSWORD = db_password
                NAME = db_name
                
                @property
                def URL(self):
                    return f"mysql+mysqlconnector://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"
            
            return EdgeDatabaseConfig()
        except Exception as e:
            # 如果获取失败，返回默认配置
            print(f"Failed to get DB config from Edge Config: {e}")
            return config.db
except ImportError:
    # 如果无法导入edge_config，定义一个模拟函数
    async def get_db_config_from_edge():
        return config.db

# Redis配置
class RedisConfig:
    HOST = os.environ.get("REDIS_HOST", "localhost")
    PORT = int(os.environ.get("REDIS_PORT", "6379"))
    PASSWORD = os.environ.get("REDIS_PASSWORD", "")
    DB = int(os.environ.get("REDIS_DB", "0"))
    
    @property
    def URL(self):
        if self.PASSWORD:
            return f"redis://:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.DB}"
        else:
            return f"redis://{self.HOST}:{self.PORT}/{self.DB}"

# API服务配置
class APISettings:
    DEBUG = os.environ.get("DEBUG", "True").lower() == "true"
    PORT = int(os.environ.get("PORT", "8080"))
    HOST = os.environ.get("HOST", "0.0.0.0")
    WORKERS = int(os.environ.get("WORKERS", "4"))
    
    # JWT配置
    SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key")
    ALGORITHM = os.environ.get("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# 微服务配置
class MicroserviceConfig:
    RULE_SERVICE_URL = os.environ.get("RULE_SERVICE_URL", "http://localhost:8000")
    NEWS_SERVICE_URL = os.environ.get("NEWS_SERVICE_URL", "http://localhost:8001")
    CALCULATION_SERVICE_URL = os.environ.get("CALCULATION_SERVICE_URL", "http://localhost:8002")
    FUND_SERVICE_URL = os.environ.get("FUND_SERVICE_URL", "http://localhost:8003")

# 日志配置
class LogConfig:
    LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    FILE = os.environ.get("LOG_FILE", None)  # 如果为None则只输出到控制台

# 爬虫配置
class CrawlerConfig:
    USER_AGENT = os.environ.get(
        "USER_AGENT", 
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36"
    )
    MAX_CONCURRENT_REQUESTS = int(os.environ.get("MAX_CONCURRENT_REQUESTS", "10"))
    REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "10"))
    RETRY_TIMES = int(os.environ.get("RETRY_TIMES", "3"))
    
    # 新闻源配置
    NEWS_SOURCES = {
        "xinhua": "http://www.xinhuanet.com/rss/xh_politics.xml",
        "people": "http://www.people.com.cn/rss/politics.xml",
        "climate_change": "https://www.ipcc.ch/news_and_events/",
        "green_energy": "https://www.irena.org/news"
    }

# 计算服务配置
class CalculationConfig:
    # 净值计算配置
    MAX_DAILY_CHANGE = float(os.environ.get("MAX_DAILY_CHANGE", "0.1"))  # 每日最大变化10%
    MIN_NET_VALUE = float(os.environ.get("MIN_NET_VALUE", "0.1"))  # 净值最低不低于0.1
    
    # 影响系数计算配置
    SENTIMENT_IMPACT_WEIGHT = float(os.environ.get("SENTIMENT_IMPACT_WEIGHT", "0.5"))
    TIME_DECAY_FACTOR = float(os.environ.get("TIME_DECAY_FACTOR", "0.1"))  # 时间衰减因子
    SOURCE_RELIABILITY_WEIGHT = float(os.environ.get("SOURCE_RELIABILITY_WEIGHT", "0.3"))
    KEYWORD_RELEVANCE_WEIGHT = float(os.environ.get("KEYWORD_RELEVANCE_WEIGHT", "0.2"))

# 合并所有配置
class Config:
    db = DatabaseConfig()
    redis = RedisConfig()
    api = APISettings()
    microservices = MicroserviceConfig()
    logs = LogConfig()
    crawler = CrawlerConfig()
    calculation = CalculationConfig()

# 创建全局配置实例
config = Config()