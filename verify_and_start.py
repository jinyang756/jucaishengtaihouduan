#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
聚财生态基金后端 - 环境验证与服务启动工具

此脚本用于：
1. 检查Python环境和必要依赖
2. 验证数据库连接
3. 检查Redis服务状态
4. 提供详细的错误信息和解决方案
5. 如果环境验证通过，启动API网关服务

使用方法：
    python verify_and_start.py
"""

import sys
import os
import importlib
import socket
import json
from datetime import datetime

# 定义颜色常量
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

# 检查是否在Windows环境下运行，如果是则禁用颜色输出
if os.name == 'nt':
    Colors.GREEN = ''
    Colors.YELLOW = ''
    Colors.RED = ''
    Colors.BLUE = ''
    Colors.END = ''

def print_success(message):
    """打印成功信息"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_warning(message):
    """打印警告信息"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_error(message):
    """打印错误信息"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message):
    """打印信息"""
    print(f"{Colors.BLUE}ℹ️  {message}{Colors.END}")

def check_python_version():
    """检查Python版本是否符合要求"""
    required_version = (3, 8)
    current_version = sys.version_info[:2]
    
    if current_version < required_version:
        print_error(f"Python版本过低。需要Python {required_version[0]}.{required_version[1]} 或更高版本，当前版本为 {current_version[0]}.{current_version[1]}")
        print_info("请前往 https://www.python.org/downloads/ 下载并安装最新版本的Python")
        return False
    
    print_success(f"Python版本检查通过: {current_version[0]}.{current_version[1]}.{sys.version_info[2]}")
    return True

def check_required_packages():
    """检查项目所需的关键Python包是否已安装"""
    required_packages = [
        'fastapi', 'uvicorn', 'sqlalchemy', 'mariadb', 'pydantic',
        'redis', 'python_dotenv', 'requests', 'passlib', 'bcrypt'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print_error(f"缺少以下必需的Python包: {', '.join(missing_packages)}")
        print_info("请运行以下命令安装所有依赖:")
        print_info("    pip install -r requirements.txt")
        return False
    
    print_success(f"所有关键Python包已安装 ({len(required_packages)}个包)")
    return True

def check_database_connection():
    """检查数据库连接是否正常"""
    # 从环境变量或默认值获取数据库配置
    db_config = {
        "host": os.environ.get("DB_HOST", "localhost"),
        "port": int(os.environ.get("DB_PORT", "3306")),
        "user": os.environ.get("DB_USER", "root"),
        "password": os.environ.get("DB_PASSWORD", "password"),
        "name": os.environ.get("DB_NAME", "green_ecology_fund")
    }
    
    print_info(f"尝试连接数据库: {db_config['user']}@{db_config['host']}:{db_config['port']}/{db_config['name']}")
    
    try:
        import mariadb
        
        # 尝试创建数据库连接
        conn = mariadb.connect(
            host=db_config['host'],
            port=db_config['port'],
            user=db_config['user'],
            password=db_config['password'],
            database=db_config['name']
        )
        conn.close()
        print_success("数据库连接成功")
        return True
    except mariadb.Error as e:
        print_error(f"数据库连接失败: {str(e)}")
        print_info("请检查以下几点:")
        print_info("1. MariaDB服务是否已启动")
        print_info("2. 数据库配置是否正确")
        print_info("3. 数据库用户是否有访问权限")
        print_info("4. 防火墙是否阻止了连接")
        print_info("\n如果需要修改数据库配置，可以设置以下环境变量:")
        print_info("    set DB_HOST=localhost")
        print_info("    set DB_PORT=3306")
        print_info("    set DB_USER=root")
        print_info("    set DB_PASSWORD=password")
        print_info("    set DB_NAME=green_ecology_fund")
        return False
    except ImportError:
        print_error("未安装mariadb包")
        print_info("请运行: pip install mariadb")
        return False

def check_redis_connection():
    """检查Redis连接是否正常"""
    redis_config = {
        "host": os.environ.get("REDIS_HOST", "localhost"),
        "port": int(os.environ.get("REDIS_PORT", "6379")),
        "password": os.environ.get("REDIS_PASSWORD", ""),
        "db": int(os.environ.get("REDIS_DB", "0"))
    }
    
    print_info(f"尝试连接Redis: {redis_config['host']}:{redis_config['port']}/db{redis_config['db']}")
    
    try:
        import redis
        
        # 尝试创建Redis连接
        client = redis.Redis(
            host=redis_config['host'],
            port=redis_config['port'],
            password=redis_config['password'],
            db=redis_config['db'],
            decode_responses=True,
            socket_connect_timeout=2
        )
        client.ping()
        print_success("Redis连接成功")
        return True
    except redis.ConnectionError as e:
        print_warning(f"Redis连接失败: {str(e)}")
        print_info("注意: Redis是可选组件，部分功能可能无法使用")
        print_info("如果需要使用Redis，请确保Redis服务已启动")
        return True  # Redis是可选的，不阻止服务启动
    except ImportError:
        print_warning("未安装redis包")
        print_info("注意: Redis是可选组件，部分功能可能无法使用")
        return True  # Redis是可选的，不阻止服务启动

def check_database_tables():
    """检查数据库表是否已创建"""
    try:
        from sqlalchemy import create_engine, inspect
        from database.database import get_database_url
        
        # 创建数据库引擎
        database_url = get_database_url()
        engine = create_engine(database_url)
        
        # 创建inspector对象检查数据库表
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        required_tables = ['users', 'funds', 'user_holdings', 'transactions']
        
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print_error(f"缺少必需的数据库表: {', '.join(missing_tables)}")
            print_info("请运行初始化脚本创建数据库表")
            print_info("您可以在api_gateway/app.py中找到init_db函数调用")
            return False
        
        print_success(f"所有必需的数据库表都已创建 ({len(tables)}个表)")
        return True
    except Exception as e:
        print_error(f"检查数据库表时出错: {str(e)}")
        print_info("请确保数据库已正确初始化")
        return False

def start_api_gateway():
    """启动API网关服务"""
    print_info("正在启动API网关服务...")
    
    try:
        # 设置环境变量，确保服务使用正确的配置
        os.environ.setdefault("ALLOWED_ORIGINS", "http://localhost,http://localhost:3000")
        os.environ.setdefault("API_GATEWAY_HOST", "0.0.0.0")
        os.environ.setdefault("API_GATEWAY_PORT", "8080")
        
        # 使用subprocess启动uvicorn服务，避免当前进程被阻塞
        import subprocess
        
        # 获取主机和端口配置
        host = os.environ.get("API_GATEWAY_HOST", "0.0.0.0")
        port = os.environ.get("API_GATEWAY_PORT", "8080")
        
        print_success(f"API网关服务将在 http://{host}:{port} 启动")
        print_info("服务启动后，您可以访问 http://localhost:8080/docs 查看API文档")
        print_info("按 Ctrl+C 停止服务")
        
        # 启动服务
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "api_gateway.app:app", 
            "--host", host, 
            "--port", port
        ])
        
    except Exception as e:
        print_error(f"启动API网关服务时出错: {str(e)}")
        print_info("您也可以尝试手动启动服务:")
        print_info("    python -m uvicorn api_gateway.app:app --host 0.0.0.0 --port 8080")
        return False

def main():
    """主函数"""
    print(f"\n{Colors.BLUE}===== 聚财生态基金后端 - 环境验证与服务启动工具 ====={Colors.END}\n")
    print_info(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"当前目录: {os.getcwd()}")
    print_info(f"Python路径: {sys.executable}\n")
    
    # 验证环境
    checks = [
        check_python_version,
        check_required_packages,
        check_database_connection,
        check_database_tables,
        check_redis_connection
    ]
    
    all_checks_passed = True
    for check in checks:
        if not check():
            all_checks_passed = False
        print()  # 打印空行分隔不同的检查
    
    # 如果所有检查都通过，启动服务
    if all_checks_passed:
        print_success("所有环境检查都已通过！")
        start_api_gateway()
    else:
        print_error("环境检查未通过，无法启动服务")
        print_info("请根据上面的错误信息修复问题后，再次运行此脚本")
        
if __name__ == "__main__":
    main()