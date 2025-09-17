import asyncio
import sys
import os

# 添加api目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'api'))

# 导入我们自定义的EdgeConfig类
from vercel_edge_config import EdgeConfig

async def test_edge_config():
    print("测试自定义EdgeConfig模块...")
    
    # 初始化EdgeConfig客户端
    edge_config = EdgeConfig()
    
    # 测试get方法
    greeting = await edge_config.get('greeting')
    print(f"获取greeting配置: {greeting}")
    
    # 测试不存在的键
    non_existent = await edge_config.get('non_existent', '默认值')
    print(f"获取不存在的键: {non_existent}")
    
    # 测试getAll方法
    all_configs = await edge_config.getAll()
    print(f"获取所有配置: {all_configs}")
    
    print("测试完成!")

if __name__ == '__main__':
    # 运行异步测试
    asyncio.run(test_edge_config())