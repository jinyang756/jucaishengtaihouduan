print("Python环境测试")
import sys
print(f"Python版本: {sys.version}")
print(f"当前路径: {__file__}")
try:
    import sqlalchemy
    print(f"SQLAlchemy版本: {sqlalchemy.__version__}")
except ImportError:
    print("未找到SQLAlchemy模块")