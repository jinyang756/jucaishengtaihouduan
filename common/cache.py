import redis
import json
from datetime import timedelta
import os

class RedisCache:
    def __init__(self):
        self.host = os.environ.get("REDIS_HOST", "localhost")
        self.port = int(os.environ.get("REDIS_PORT", 6379))
        self.password = os.environ.get("REDIS_PASSWORD", "")
        self.db = int(os.environ.get("REDIS_DB", 0))
        self.client = self._connect()
    
    def _connect(self):
        """连接Redis"""
        try:
            return redis.Redis(
                host=self.host,
                port=self.port,
                password=self.password,
                db=self.db,
                decode_responses=True
            )
        except Exception as e:
            print(f"Redis connection error: {str(e)}")
            return None
    
    def get(self, key: str):
        """获取缓存数据"""
        if not self.client:
            return None
        
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"Redis get error: {str(e)}")
            return None
    
    def set(self, key: str, value: dict, expire_seconds: int = 3600):
        """设置缓存数据"""
        if not self.client:
            return False
        
        try:
            self.client.setex(
                key,
                timedelta(seconds=expire_seconds),
                json.dumps(value)
            )
            return True
        except Exception as e:
            print(f"Redis set error: {str(e)}")
            return False
    
    def delete(self, key: str):
        """删除缓存数据"""
        if not self.client:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Redis delete error: {str(e)}")
            return False
    
    def clear_pattern(self, pattern: str):
        """删除匹配模式的缓存"""
        if not self.client:
            return False
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
            return True
        except Exception as e:
            print(f"Redis clear pattern error: {str(e)}")
            return False

# 创建缓存实例
cache = RedisCache()