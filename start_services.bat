REM 聚财生态基金后端服务启动脚本

REM 设置中文显示
chcp 65001

@echo off

cls
echo ===========================================================
echo 聚财生态基金后端 - 服务启动脚本
echo ===========================================================
echo.

REM 检查是否已安装Docker
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Docker，请先安装Docker Desktop
    echo 下载地址: https://www.docker.com/get-started
    pause
    exit /b 1
)

REM 检查是否已安装Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 未找到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 如果.env文件不存在，创建它
if not exist .env (
    echo 正在创建.env配置文件...
    copy .env.example .env
    echo .env文件已创建，使用默认配置
)

REM 清理旧的容器和网络
echo.
echo 正在清理旧的容器和网络...
docker-compose down

REM 构建和启动服务
echo.
echo 正在构建和启动服务...
docker-compose up -d --build

REM 等待服务启动
echo.
echo 等待服务启动...
timeout /t 10 /nobreak >nul

REM 运行环境验证脚本
echo.
echo 正在运行环境验证脚本...
python verify_environment.py

REM 显示服务状态
echo.
echo ===========================================================
echo 服务启动完成！您可以通过以下地址访问服务：
echo.
echo API网关: http://localhost:8080
echo 规则服务: http://localhost:8000
echo 新闻服务: http://localhost:8001
echo 计算服务: http://localhost:8002
echo 基金服务: http://localhost:8003
echo MariaDB数据库: localhost:3306 (用户名: root, 密码: password)
echo Redis: localhost:6379
echo Prometheus监控: http://localhost:9090
echo Grafana可视化: http://localhost:3000 (用户名: admin, 密码: admin)
echo ===========================================================
echo.
echo 下一步：进行功能测试，验证各服务的业务逻辑是否正常工作。
echo 要停止所有服务，请运行：docker-compose down
echo.

pause