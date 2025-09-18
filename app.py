from api.index import app as application

# 这是一个用于 Vercel CLI 的兼容层
# 它会导入 api/index.py 中的 FastAPI 应用
# 确保 Vercel CLI 能够正确识别入口点

# 保持原有的开发环境运行配置
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = os.environ.get("RELOAD", "True").lower() == "true"
    uvicorn.run("app:application", host=host, port=port, reload=reload)