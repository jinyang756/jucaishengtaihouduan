from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from mangum import Mangum
import os
from dotenv import load_dotenv
import logging

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("vercel_api")

# 创建FastAPI应用
app = FastAPI(
    title="聚财生态基金系统",
    description="绿色生态基金虚拟净值模拟系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 导入和集成user_service
# 注意：由于user_service使用了独立的FastAPI应用实例，我们将创建一个新的路由来集成它
user_service_router = APIRouter(prefix="/api/users", tags=["用户服务"])

# 导入user_service的功能
from user_service.service import (
    register_user as user_service_register_user,
    login_user as user_service_login_user,
    get_user as user_service_get_user_by_id,
    update_user as user_service_update_user,
    update_balance as user_service_deposit_balance,
    get_user_holdings as user_service_get_user_holdings,
    get_user_transactions as user_service_get_user_transactions,
    create_transaction as user_service_create_transaction
)
from user_service.schemas import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    UserUpdateRequest,
    BalanceUpdateRequest,
    HoldingResponse,
    TransactionCreateRequest,
    TransactionResponse,
    PaginatedTransactionsResponse
)
from database.database import get_db
from sqlalchemy.orm import Session
from fastapi import Depends

# 重新定义user_service的API路由
@user_service_router.post("/register", response_model=UserResponse)
def register_user_endpoint(user_data: UserRegisterRequest, db: Session = Depends(get_db)):
    return user_service_register_user(user_data, db)

@user_service_router.post("/login")
def login_user_endpoint(login_data: UserLoginRequest, db: Session = Depends(get_db)):
    return user_service_login_user(login_data, db)

@user_service_router.get("/{user_id}", response_model=UserResponse)
def get_user_by_id_endpoint(user_id: str, db: Session = Depends(get_db)):
    return user_service_get_user_by_id(user_id, db)

@user_service_router.put("/{user_id}", response_model=UserResponse)
def update_user_endpoint(user_id: str, user_data: UserUpdateRequest, db: Session = Depends(get_db)):
    return user_service_update_user(user_id, user_data, db)

@user_service_router.post("/{user_id}/balance/deposit")
def deposit_balance_endpoint(user_id: str, balance_data: BalanceUpdateRequest, db: Session = Depends(get_db)):
    return user_service_deposit_balance(user_id, balance_data, db)

@user_service_router.get("/{user_id}/holdings", response_model=List[HoldingResponse])
def get_user_holdings_endpoint(user_id: str, db: Session = Depends(get_db)):
    return user_service_get_user_holdings(user_id, db)

@user_service_router.get("/{user_id}/transactions", response_model=PaginatedTransactionsResponse)
def get_user_transactions_endpoint(user_id: str, page: int = 1, per_page: int = 10, db: Session = Depends(get_db)):
    return user_service_get_user_transactions(user_id, page, per_page, db)

@user_service_router.post("/transactions", response_model=TransactionResponse)
def create_transaction_endpoint(transaction_data: TransactionCreateRequest, db: Session = Depends(get_db)):
    return user_service_create_transaction(transaction_data, db)

# 将user_service路由挂载到主应用
app.include_router(user_service_router)

# 添加CORS中间件
origins = [
    "*",  # 生产环境应替换为具体的前端URL
    os.environ.get("FRONTEND_URL", ""),
    "http://localhost:3000",
    "http://localhost:8080"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 根路径端点
@app.get("/")
def root():
    """根路径，返回系统信息"""
    return {
        "app": "聚财生态基金系统API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

# 健康检查端点
@app.get("/health")
def health_check():
    """健康检查端点"""
    try:
        # 简单检查环境变量是否加载
        db_name = os.environ.get("DB_NAME", "未配置")
        return {
            "status": "healthy",
            "environment": os.environ.get("VERCEL_ENV", "development"),
            "database": db_name,
            "message": "系统运行正常"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Edge Config测试端点
@app.get("/welcome")
def welcome():
    """测试Edge Config集成"""
    try:
        # 尝试获取Edge Config值
        welcome_message = os.environ.get("WELCOME_MESSAGE", "欢迎使用聚财生态基金系统")
        return {
            "message": welcome_message,
            "source": "environment variable"
        }
    except Exception as e:
        logger.error(f"Welcome endpoint error: {str(e)}")
        return {
            "message": "欢迎使用聚财生态基金系统",
            "source": "fallback",
            "error": str(e)
        }

# 导出为Vercel Serverless Function
handler = Mangum(app)

# 注意：其他服务（fund_service, calculation_service, news_service, rule_service）
# 目前保留原样，但在未来可以按照类似user_service的方式集成到主API中
# 这种集成方式可以避免多个独立FastAPI应用实例导致的冲突
# 同时保留了完整的user_service功能和代码结构

# 本地开发环境运行时的配置
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = os.environ.get("RELOAD", "True").lower() == "true"
    logger.info(f"Starting API on {host}:{port}")
    uvicorn.run("index:app", host=host, port=port, reload=reload)