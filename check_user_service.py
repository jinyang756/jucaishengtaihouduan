import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 尝试导入user_service模块
try:
    print("尝试导入user_service.service...")
    from user_service import service
    print("成功导入user_service.service")
    
    print("尝试导入user_service.models...")
    from user_service import models
    print("成功导入user_service.models")
    
    print("尝试导入user_service.schemas...")
    from user_service import schemas
    print("成功导入user_service.schemas")
    
    print("\n✅ 所有模块导入成功，没有语法错误！")
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    sys.exit(1)
except SyntaxError as e:
    print(f"❌ 语法错误: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ 发生错误: {e}")
    sys.exit(1)