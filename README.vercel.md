# Vercel部署指南

## 项目概述
本指南提供了在Vercel平台上部署聚财生态基金后端系统的详细步骤和配置说明。

## 已完成的配置修改

1. **项目结构调整**
   - 创建了`api/`目录作为Serverless Functions入口点
   - 添加了`api/index.py`作为主入口文件
   - 添加了`api/requirements.txt`包含必要的依赖
   - 添加了`api/.env.example`环境变量示例文件

2. **部署配置更新**
   - 更新了`vercel.json`，将：
     - 添加了`app.py`作为Vercel CLI的识别入口
     - 添加了`api/index.py`作为实际运行入口
     - 路由规则更新为指向`app.py`
     - 构建命令配置从`build.commands`改为`installCommand`和`buildCommand`
     - 配置了合适的函数内存(1024MB)和执行超时(30秒)

3. **创建Vercel CLI兼容层**
   - 修改了根目录的`app.py`文件，作为兼容层
   - 它会导入`api/index.py`中的FastAPI应用
   - 确保Vercel CLI能够正确识别入口点

## 本地测试方法

在部署到Vercel之前，建议在本地测试Serverless入口点：

```bash
# 进入api目录
cd api

# 安装依赖
pip install -r requirements.txt

# 运行Serverless入口点
python index.py
```

测试端点：
- 根路径: http://localhost:8080/
- 健康检查: http://localhost:8080/health
- API文档: http://localhost:8080/docs

## Vercel部署步骤

1. **准备工作**
   - 确保您已拥有Vercel账号
   - 确保项目已推送到GitHub/GitLab等代码托管平台
   - 准备好数据库连接信息

2. **环境变量配置**
在Vercel项目设置中添加以下环境变量：

| 环境变量 | 说明 | 示例值 |
|---------|------|-------|
| DATABASE_URL | 数据库连接URL | mariadb+mariadbconnector://username:password@host:port/database_name |
| DB_HOST | 数据库主机 | your-database-host.com |
| DB_PORT | 数据库端口 | 3306 |
| DB_USER | 数据库用户名 | your-username |
| DB_PASSWORD | 数据库密码 | your-password |
| DB_NAME | 数据库名称 | green_ecology_fund |
| SECRET_KEY | 应用密钥 | your-secret-key |
| JWT_SECRET_KEY | JWT密钥 | your-jwt-secret-key |
| PYTHON_VERSION | Python版本 | 3.9 |

3. **部署流程**
   - 在Vercel控制台导入您的Git仓库
   - Vercel会自动识别`vercel.json`配置
   - 等待部署完成并测试端点

## 部署注意事项

1. **性能优化**
   - Serverless函数有冷启动延迟，首次访问可能较慢
   - 考虑使用Vercel的Edge Functions获得更好的性能

2. **资源限制**
   - 函数内存限制为1024MB
   - 函数执行时间限制为30秒

3. **数据库连接**
   - 确保数据库允许从Vercel IP地址访问
   - 考虑使用连接池来优化数据库连接

4. **日志与监控**
   - 在Vercel控制台查看函数日志
   - 配置适当的错误处理和日志记录

## 故障排查

常见部署问题及解决方案：

1. **部署失败**
   - 检查`api/requirements.txt`中的依赖是否正确
   - 验证`vercel.json`格式是否正确
   - 查看Vercel构建日志了解具体错误

2. **数据库连接问题**
   - 确认环境变量中的数据库连接信息正确
   - 验证数据库服务器允许远程连接
   - 检查网络防火墙设置

3. **函数超时**
   - 优化长时间运行的操作
   - 考虑使用异步处理
   - 检查数据库查询性能

## 相关资源

- [Vercel Python Serverless Functions文档](https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [Mangum文档](https://mangum.io/)