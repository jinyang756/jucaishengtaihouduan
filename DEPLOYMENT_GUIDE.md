# 聚财生态基金后端 Vercel 部署指南

本文件记录了成功部署到Vercel平台的关键配置和路径，供后续参考。

## 成功部署的关键配置文件

### 1. 项目入口文件 (app.py)
```python
# 这是Vercel CLI的兼容层文件
# 用于确保Vercel能够正确识别和运行FastAPI应用
import uvicorn
from api.index import app, handler

# 定义application变量，Vercel会寻找这个变量作为入口
application = app

# 导出handler，这是Mangum处理程序，用于无服务器环境
__all__ = ['handler', 'app', 'application']

# 本地开发环境运行配置
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8080, reload=True)
```

### 2. Vercel配置文件 (vercel.json)
```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ],
  "env": {},
  "installCommand": "pip install -r requirements.txt",
  "buildCommand": "echo 'No build needed'"
}
```

### 3. 依赖配置文件 (requirements.txt)
```txt
# 精简版依赖，仅包含Vercel部署所需的基本包
fastapi==0.95.2
uvicorn==0.22.0
mangum==0.17.0
python-dotenv==1.0.0
pydantic==1.10.12
python-multipart==0.0.6
```

### 4. FastAPI主应用文件 (api/index.py)
包含健康检查端点和主要API路由，使用Mangum包装以支持Vercel无服务器环境。

## 部署步骤

1. 确保上述配置文件正确设置
2. 运行 `vercel deploy` 命令部署到预览环境
3. 运行 `vercel --prod` 命令部署到生产环境

## 预览链接
https://jucaishengtaihouduan-hp4smnae1-kims-projects-005a1207.vercel.app

## 注意事项

1. 生产环境部署前，请确保所有API端点都经过充分测试
2. 如需要数据库连接或其他服务，请在Vercel环境变量中配置相关信息
3. 当前配置移除了需要编译环境的依赖，确保了在Vercel容器中能够顺利构建