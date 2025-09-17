#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""环境验证脚本 - 用于检查Docker容器运行状态、数据库连接和数据初始化情况"""
import subprocess
import sys
import time
import mariadb

def check_docker_containers():
    """检查Docker容器运行状态"""
    print("===== 检查Docker容器运行状态 ======")
    try:
        # 检查容器是否运行
        result = subprocess.run(['docker', 'compose', 'ps'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Docker Compose 命令执行失败")
            print(result.stderr)
            return False
        
        output = result.stdout
        containers = ['mariadb', 'redis', 'api_gateway', 'rule_service', 'news_service', 'calculation_service', 'fund_service']
        
        for container in containers:
            if container in output:
                if 'Up' in output.split(container)[1].split('\n')[0]:
                    print(f"✅ {container} 容器正在运行")
                else:
                    print(f"❌ {container} 容器未正常运行")
                    return False
            else:
                print(f"❌ {container} 容器未找到")
                return False
        
        print("✅ 所有必要的Docker容器均已正常运行")
        return True
    except Exception as e:
        print(f"❌ 检查Docker容器时出错: {str(e)}")
        return False

def wait_for_database():
    """等待数据库初始化完成"""
    print("\n===== 等待数据库初始化完成 ======")
    max_retries = 30
    retry_interval = 2
    
    for i in range(max_retries):
        try:
            # 检查MariaDB健康状态
            result = subprocess.run(
                ['docker', 'compose', 'exec', '-T', 'mariadb', 'mysqladmin', 'ping', '-h', 'localhost', '-u', 'root', '-ppassword'],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                print("✅ MariaDB 数据库已准备就绪")
                return True
            
            if i % 5 == 0:
                print(f"⌛ 等待数据库初始化... ({i*retry_interval}/{max_retries*retry_interval}秒)")
            
        except Exception as e:
            if i % 5 == 0:
                print(f"⌛ 数据库尚未就绪: {str(e)}")
                
        time.sleep(retry_interval)
    
    print("❌ 数据库初始化超时")
    return False

def check_database_connection():
    """检查数据库连接和数据初始化"""
    print("\n===== 检查数据库连接和数据初始化 ======")
    try:
        # 连接数据库
        conn = mariadb.connect(
            host='localhost',
            port=3306,
            user='root',
            password='password',
            database='green_ecology_fund'
        )
        
        with conn.cursor() as cursor:
            # 检查数据库是否存在
            cursor.execute("SHOW DATABASES LIKE 'green_ecology_fund'")
            if cursor.fetchone() is None:
                print("❌ 数据库 'green_ecology_fund' 不存在")
                return False
            
            print("✅ 数据库 'green_ecology_fund' 已创建")
            
            # 检查表是否存在
            tables = ['rules', 'news', 'calculation_logs', 'news_impacts', 'funds', 'fund_net_values']
            for table in tables:
                cursor.execute(f"SHOW TABLES LIKE '{table}'")
                if cursor.fetchone() is None:
                    print(f"❌ 表 '{table}' 不存在")
                    return False
                
                print(f"✅ 表 '{table}' 已创建")
                
                # 检查是否有数据
                cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                count = cursor.fetchone()['count']
                print(f"   表 '{table}' 中有 {count} 条记录")
                
                if table == 'funds' and count == 0:
                    print(f"❌ 表 '{table}' 应该有示例数据，但目前为空")
                    return False
        
        conn.close()
        print("✅ 所有数据库表都已正确创建并包含预期数据")
        return True
        
    except Exception as e:
        print(f"❌ 检查数据库时出错: {str(e)}")
        return False

def check_api_health():
    """检查API服务健康状态"""
    print("\n===== 检查API服务健康状态 ======")
    try:
        # 检查API网关是否响应
        result = subprocess.run(
            ['curl', '-s', 'http://localhost:8080/welcome'],
            capture_output=True, text=True
        )
        
        if result.returncode == 0:
            print("✅ API网关服务响应正常")
            print(f"   响应内容: {result.stdout.strip()}")
        else:
            print("❌ API网关服务未正常响应")
            print(f"   错误: {result.stderr}")
            return False
        
        # 检查各个微服务
        services = [
            ('规则服务', 'http://localhost:8000'),
            ('新闻服务', 'http://localhost:8001'),
            ('计算服务', 'http://localhost:8002'),
            ('基金服务', 'http://localhost:8003')
        ]
        
        for name, url in services:
            try:
                result = subprocess.run(
                    ['curl', '-s', f'{url}/ping'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0 and 'pong' in result.stdout.lower():
                    print(f"✅ {name} 响应正常")
                else:
                    print(f"⚠️ {name} 响应不正常或未实现ping端点")
            except subprocess.TimeoutExpired:
                print(f"❌ {name} 连接超时")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查API服务时出错: {str(e)}")
        return False

def main():
    """主函数"""
    print("===== 聚财生态基金后端环境验证开始 =====")
    
    # 1. 检查Docker容器
    if not check_docker_containers():
        print("\n❌ 环境验证失败: Docker容器未正常运行")
        sys.exit(1)
    
    # 2. 等待数据库初始化完成
    if not wait_for_database():
        print("\n❌ 环境验证失败: 数据库初始化超时")
        sys.exit(1)
    
    # 3. 检查数据库连接和数据初始化
    if not check_database_connection():
        print("\n❌ 环境验证失败: 数据库配置或初始化有问题")
        sys.exit(1)
    
    # 4. 检查API服务健康状态
    check_api_health()
    
    print("\n===== 聚财生态基金后端环境验证完成 =====")
    print("✅ 所有核心组件验证通过，环境准备就绪！")
    print("\n下一步：可以开始功能测试，验证各服务的业务逻辑是否正常工作。")

if __name__ == "__main__":
    main()