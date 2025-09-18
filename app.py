from api.index import app as application

# 这是一个用于 Vercel CLI 的兼容层
# 它会导入 api/index.py 中的 FastAPI 应用和Mangum处理器
# 确保 Vercel CLI 能够正确识别入口点

# 从 api/index.py 导入应用和处理器
from api.index import app, handler

# 为了保持与Vercel的兼容性，定义application变量
application = app

# 导出handler以支持Vercel Serverless Function
if __name__ == "app":
    # 这是为了在Vercel环境中正确导出handler
    pass

# 确保handler可被导入
handler = handler

# 保持原有的开发环境运行配置
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = os.environ.get("RELOAD", "True").lower() == "true"
    uvicorn.run("app:application", host=host, port=port, reload=reload)