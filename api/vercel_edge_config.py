import os
import httpx
import asyncio
import re

class EdgeConfig:
    def __init__(self, connection_string=None):
        # 从环境变量或参数获取Edge Config连接信息
        self.connection_string = connection_string or os.environ.get('EDGE_CONFIG')
        self.base_url = os.environ.get('VERCEL_URL', 'http://localhost:3000')
        self.edge_config_id = os.environ.get('EDGE_CONFIG_ID')
        self.edge_config_token = os.environ.get('EDGE_CONFIG_TOKEN')
        
        # 如果没有提供连接字符串，使用默认值或模拟行为
        if not self.connection_string and not self.edge_config_token:
            # 在开发环境下，我们可以提供一个默认的模拟实现
            self.is_mock = True
            # 模拟Edge Config中的默认值
            self.mock_data = {
                'greeting': {'message': 'Welcome to the Green Ecology Fund API!'},
                # 添加默认的数据库配置项
                'DB_HOST': os.environ.get('DB_HOST', 'localhost'),
                'DB_PORT': os.environ.get('DB_PORT', '3306'),
                'DB_USER': os.environ.get('DB_USER', 'root'),
                'DB_PASSWORD': os.environ.get('DB_PASSWORD', 'password'),
                'DB_NAME': os.environ.get('DB_NAME', 'green_ecology_fund')
            }
        else:
            self.is_mock = False
            # 实际环境中，解析连接字符串获取必要信息
            try:
                # 从连接字符串或环境变量获取token
                if self.connection_string:
                    self.edge_config_token = self.extract_token_from_connection_string()
                    # 从连接字符串提取Edge Config ID
                    self.edge_config_id = self.extract_id_from_connection_string()
                
                # Vercel Edge Config API基础URL
                self.api_url = "https://edge-config.vercel.com"
                # Vercel REST API基础URL
                self.vercel_api_url = "https://api.vercel.com/v1/edge-config"
                self.headers = {
                    'Authorization': f'Bearer {self.edge_config_token}'
                }
            except Exception as e:
                print(f"Error parsing Edge Config connection string: {e}")
                # 解析失败时切换到模拟模式
                self.is_mock = True
                self.mock_data = {
                    'greeting': {'message': 'Welcome to the Green Ecology Fund API!'},
                    # 添加默认的数据库配置项
                    'DB_HOST': os.environ.get('DB_HOST', 'localhost'),
                    'DB_PORT': os.environ.get('DB_PORT', '3306'),
                    'DB_USER': os.environ.get('DB_USER', 'root'),
                    'DB_PASSWORD': os.environ.get('DB_PASSWORD', 'password'),
                    'DB_NAME': os.environ.get('DB_NAME', 'green_ecology_fund')
                }
    
    def extract_token_from_connection_string(self):
        # 从连接字符串提取token
        if 'token=' in self.connection_string:
            # 使用正则表达式安全地提取token
            match = re.search(r'token=([^&]+)', self.connection_string)
            if match:
                return match.group(1)
        return ''
    
    def extract_id_from_connection_string(self):
        # 从连接字符串提取Edge Config ID
        # 格式通常为 https://edge-config.vercel.com/{id}?token=...
        if self.connection_string:
            # 使用正则表达式提取ID
            match = re.search(r'vercel\.com/([^/?]+)', self.connection_string)
            if match:
                return match.group(1)
        return self.edge_config_id or ''
    
    async def get(self, key, default=None):
        """从Edge Config获取指定键的值"""
        if self.is_mock:
            # 模拟环境下直接返回模拟数据
            return self.mock_data.get(key, default)
        
        try:
            # 构建实际的Edge Config API URL
            url = f"{self.api_url}/{self.edge_config_id}/items/{key}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        # 返回值字段通常是'value'
                        return data.get('value', data) if isinstance(data, dict) else data
                    except ValueError:
                        return response.text
                elif response.status_code == 404:
                    print(f"Key {key} not found in Edge Config")
                    return default
                else:
                    print(f"Error fetching from Edge Config: {response.status_code} - {response.text}")
                    return default
        except Exception as e:
            print(f"Exception when fetching from Edge Config: {e}")
            # 出错时返回默认值
            return default
    
    def get_sync(self, key, default=None):
        """同步版本的get方法，在非异步环境中使用"""
        if self.is_mock:
            # 模拟环境下直接返回模拟数据
            return self.mock_data.get(key, default)
        
        try:
            # 使用asyncio.run来运行异步get方法
            return asyncio.run(self.get(key, default))
        except Exception as e:
            print(f"Error in sync get from Edge Config: {e}")
            return default
    
    async def getAll(self):
        """获取所有Edge Config配置项"""
        if self.is_mock:
            return self.mock_data
        
        try:
            # 构建获取所有配置项的URL
            url = f"{self.api_url}/{self.edge_config_id}/items"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        # 通常响应会包含一个'items'字段，其中包含所有键值对
                        if isinstance(data, dict) and 'items' in data:
                            return data['items']
                        return data
                    except ValueError:
                        return {}
                else:
                    print(f"Error fetching all from Edge Config: {response.status_code} - {response.text}")
                    return {}
        except Exception as e:
            print(f"Exception when fetching all from Edge Config: {e}")
            return {}
    
    async def listEdgeConfigs(self, teamId=None):
        """列出所有Edge配置，返回格式与Vercel REST API相同"""
        if self.is_mock:
            # 模拟返回Edge配置列表
            return [{
                "slug": "mock-edge-config",
                "itemCount": len(self.mock_data),
                "createdAt": 1700000000000,
                "updatedAt": 1700000000000,
                "id": self.edge_config_id or "ecfg_mock",
                "digest": "mock_digest",
                "sizeInBytes": 100,
                "ownerId": "user_mock"
            }]
        
        try:
            # 构建API URL，支持teamId参数
            url = self.vercel_api_url
            if teamId:
                url += f"?teamId={teamId}"
                
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        # 通常API返回的是一个Edge配置对象数组
                        if isinstance(data, list):
                            return data
                        # 也可能是一个包含Edge配置的对象，需要提取
                        elif isinstance(data, dict) and 'edgeConfigs' in data:
                            return data['edgeConfigs']
                        return []
                    except ValueError:
                        print("Invalid JSON response when listing Edge Configs")
                        return []
                else:
                    print(f"Error listing Edge Configs: {response.status_code} - {response.text}")
                    return []
        except Exception as e:
            print(f"Exception when listing Edge Configs: {e}")
            return []
    
    async def getEdgeConfigDetails(self):
        """获取当前Edge Config的详细信息"""
        if self.is_mock:
            # 模拟返回Edge配置详情
            return {
                "createdAt": 1700000000000,
                "updatedAt": 1700000000000,
                "slug": "mock-edge-config",
                "id": self.edge_config_id or "ecfg_mock",
                "digest": "mock_digest",
                "sizeInBytes": 100,
                "itemCount": len(self.mock_data),
                "ownerId": "user_mock"
            }
        
        try:
            # 使用Vercel REST API获取Edge Config详情
            url = f"{self.vercel_api_url}/{self.edge_config_id}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    try:
                        return response.json()
                    except ValueError:
                        print("Invalid JSON response for Edge Config details")
                        return {}
                else:
                    print(f"Error fetching Edge Config details: {response.status_code} - {response.text}")
                    return {}
        except Exception as e:
            print(f"Exception when fetching Edge Config details: {e}")
            return {}