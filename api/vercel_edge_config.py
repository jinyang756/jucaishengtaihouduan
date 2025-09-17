import os
import httpx
import asyncio

class EdgeConfig:
    def __init__(self, connection_string=None):
        # 从环境变量或参数获取Edge Config连接信息
        self.connection_string = connection_string or os.environ.get('EDGE_CONFIG')
        self.base_url = os.environ.get('VERCEL_URL', 'http://localhost:3000')
        
        # 如果没有提供连接字符串，使用默认值或模拟行为
        if not self.connection_string:
            # 在开发环境下，我们可以提供一个默认的模拟实现
            self.is_mock = True
            # 模拟Edge Config中的默认值
            self.mock_data = {
                'greeting': {'message': 'Welcome to the Green Ecology Fund API!'}
            }
        else:
            self.is_mock = False
            # 实际环境中，解析连接字符串获取必要信息
            # 注意：这里简化处理，实际应该解析完整的连接字符串
            # 示例连接字符串格式：https://edge-config.vercel.com/<team-id>/<item-id>?token=<token>
            try:
                self.api_url = f"{self.base_url}/api/edge-config"
                self.headers = {
                    'Authorization': f'Bearer {self.extract_token_from_connection_string()}'
                }
            except Exception as e:
                print(f"Error parsing Edge Config connection string: {e}")
                # 解析失败时切换到模拟模式
                self.is_mock = True
                self.mock_data = {
                    'greeting': {'message': 'Welcome to the Green Ecology Fund API!'}
                }
    
    def extract_token_from_connection_string(self):
        # 简化的令牌提取逻辑
        # 在实际应用中，应该使用更健壮的解析方法
        if 'token=' in self.connection_string:
            return self.connection_string.split('token=')[1]
        return ''
    
    async def get(self, key, default=None):
        """从Edge Config获取指定键的值"""
        if self.is_mock:
            # 模拟环境下直接返回模拟数据
            return self.mock_data.get(key, default)
        
        try:
            # 在实际环境中，调用Edge Config API
            async with httpx.AsyncClient() as client:
                # 注意：这里使用简化的API调用方式
                # 实际应用中，应该根据Vercel Edge Config的实际API文档来调用
                response = await client.get(
                    f"{self.api_url}/{key}",
                    headers=self.headers,
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    return default
                else:
                    print(f"Error fetching from Edge Config: {response.status_code}")
                    return default
        except Exception as e:
            print(f"Exception when fetching from Edge Config: {e}")
            # 出错时返回默认值
            return default
    
    async def getAll(self):
        """获取所有Edge Config配置项"""
        if self.is_mock:
            return self.mock_data
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.api_url,
                    headers=self.headers,
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"Error fetching all from Edge Config: {response.status_code}")
                    return {}
        except Exception as e:
            print(f"Exception when fetching all from Edge Config: {e}")
            return {}