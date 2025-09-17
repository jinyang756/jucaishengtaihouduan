from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .models import User, UserHolding, Transaction, UserStatus
from fund_service.models import Fund
from .schemas import (
    UserRegisterRequest, UserLoginRequest, UserResponse, 
    UserUpdateRequest, BalanceUpdateRequest, HoldingResponse,
    TransactionRequest, TransactionResponse, PaginatedTransactionsResponse,
    TransactionCreateRequest
)
from database.database import get_db
from common.cache import cache
import uuid
import hashlib
import json
from datetime import datetime, timedelta
import secrets
import os
from starlette import status
# 添加passlib和bcrypt用于密码哈希
from passlib.context import CryptContext
import re
import logging

# 导入配置
from config.config import config

# 配置日志
logger = logging.getLogger("user_service")

app = FastAPI(
    title="用户服务",
    description="绿色生态基金虚拟净值模拟系统的用户服务",
    version="1.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "http://localhost,http://localhost:3000").split(","),  # 从环境变量获取，默认值用于开发环境
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Authorization", 
        "Content-Type", 
        "Accept",
        "X-Request-ID"
    ],
    expose_headers=["Content-Disposition", "X-Total-Count"],
    max_age=600  # 预检请求的缓存时间（秒）
)

# 创建密码上下文对象，使用bcrypt算法
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=14)  # 增加rounds参数增强安全性

# 密码复杂度验证函数
def validate_password_strength(password: str) -> tuple[bool, str]:
    """验证密码复杂度
    要求：
    - 至少8个字符
    - 包含至少一个大写字母
    - 包含至少一个小写字母
    - 包含至少一个数字
    - 包含至少一个特殊字符
    """
    if len(password) < 8:
        return False, "密码长度至少为8个字符"
    if not re.search(r"[A-Z]", password):
        return False, "密码必须包含至少一个大写字母"
    if not re.search(r"[a-z]", password):
        return False, "密码必须包含至少一个小写字母"
    if not re.search(r"[0-9]", password):
        return False, "密码必须包含至少一个数字"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "密码必须包含至少一个特殊字符"
    return True, "密码复杂度符合要求"

# 密码加密函数
def hash_password(password: str) -> str:
    """使用bcrypt算法对密码进行哈希处理"""
    # 先验证密码复杂度
    is_valid, message = validate_password_strength(password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    return pwd_context.hash(password)

# 密码验证函数
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码是否匹配"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"密码验证失败: {str(e)}")
        return False

# 生成会话ID
def generate_session_id() -> str:
    return secrets.token_urlsafe(32)

# 用户注册
def register_user(user_data: UserRegisterRequest, db: Session) -> UserResponse:
    """用户注册功能"""
    # 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # 检查邮箱是否已存在
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 创建新用户
    new_user = User(
        id=str(uuid.uuid4()),
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        phone=user_data.phone,
        balance=10000.0  # 注册时赠送10000元模拟资金
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse.from_orm(new_user)

# 用户登录
def login_user(login_data: UserLoginRequest, db: Session) -> dict:
    """用户登录功能"""
    # 查找用户
    user = db.query(User).filter(User.username == login_data.username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # 验证密码
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # 检查用户状态
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    # 更新最后登录时间
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # 生成会话ID
    session_id = generate_session_id()
    
    # 将会话存储在Redis中（有效期24小时）
    session_data = {
        "user_id": user.id,
        "username": user.username,
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat()
    }
    cache.set(f"session:{session_id}", session_data, 86400)
    
    return {
        "session_id": session_id,
        "user": UserResponse.from_orm(user)
    }

# 获取用户信息
def get_user(user_id: str, db: Session) -> UserResponse:
    """获取用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.from_orm(user)

# 更新用户信息
def update_user(user_id: str, update_data: UserUpdateRequest, db: Session) -> UserResponse:
    """更新用户信息"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 更新用户字段
    for key, value in update_data.dict(exclude_unset=True).items():
        if key == "email":
            # 检查新邮箱是否已被使用
            existing_email = db.query(User).filter(User.email == value, User.id != user_id).first()
            if existing_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
        setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    
    return UserResponse.from_orm(user)

# 更新用户余额
def update_balance(user_id: str, update_data: BalanceUpdateRequest, operation_type: str, db: Session):
    """
    更新用户余额
    使用事务确保数据一致性
    """
    try:
        # 开始事务
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        amount = update_data.amount
        
        if operation_type == "deposit":
            user.balance += amount
        elif operation_type == "withdraw":
            if user.balance < amount:
                raise HTTPException(status_code=400, detail="Insufficient balance")
            user.balance -= amount
        else:
            raise HTTPException(status_code=400, detail="Invalid operation type")
        
        db.commit()
        db.refresh(user)
        return user.balance
    except Exception as e:
        # 发生异常时回滚事务
        db.rollback()
        # 如果是我们主动抛出的HTTPException，重新抛出
        if isinstance(e, HTTPException):
            raise
        # 其他异常转为500错误
        raise HTTPException(status_code=500, detail=f"Failed to update balance: {str(e)}")

# 创建交易
def create_transaction(user_id: str, transaction_data: TransactionCreateRequest, db: Session):
    """
    创建交易记录
    使用事务确保数据一致性
    包含交易限额检查
    """
    try:
        # 开始事务
        # 检查用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 检查基金是否存在
        fund = db.query(Fund).filter(Fund.id == transaction_data.fund_id).first()
        if not fund:
            raise HTTPException(status_code=404, detail="Fund not found")
        
        # 计算交易金额
        transaction_amount = transaction_data.shares * fund.latest_nav
        
        # 交易限额检查
        if config.user.ENABLE_TRANSACTION_LIMITS:
            # 获取当日开始时间
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            
            # 单笔交易限额检查
            if transaction_amount > config.user.MAX_SINGLE_TRANSACTION_AMOUNT:
                raise HTTPException(
                    status_code=400,
                    detail=f"Single transaction amount exceeds limit: {config.user.MAX_SINGLE_TRANSACTION_AMOUNT}"
                )
            
            # 查询当日已发生的交易
            today_transactions = db.query(Transaction).filter(
                Transaction.user_id == user_id,
                Transaction.transaction_date >= today_start,
                Transaction.status == "completed"
            ).all()
            
            # 计算当日累计交易金额和交易笔数
            daily_transaction_amount = sum(t.amount for t in today_transactions)
            daily_transaction_count = len(today_transactions)
            
            # 每日交易金额限额检查
            if daily_transaction_amount + transaction_amount > config.user.MAX_DAILY_TRANSACTION_AMOUNT:
                raise HTTPException(
                    status_code=400,
                    detail=f"Daily transaction amount exceeds limit: {config.user.MAX_DAILY_TRANSACTION_AMOUNT}"
                )
            
            # 每日交易笔数限额检查
            if daily_transaction_count >= config.user.MAX_DAILY_TRANSACTION_COUNT:
                raise HTTPException(
                    status_code=400,
                    detail=f"Daily transaction count exceeds limit: {config.user.MAX_DAILY_TRANSACTION_COUNT}"
                )
        
        # 根据交易类型执行不同的逻辑
        if transaction_data.transaction_type == "buy":
            # 检查余额是否充足
            if user.balance < transaction_amount:
                raise HTTPException(status_code=400, detail="Insufficient balance")
            # 扣减余额
            user.balance -= transaction_amount
            
            # 更新用户持仓
            holding = db.query(UserHolding).filter(
                UserHolding.user_id == user_id, 
                UserHolding.fund_id == transaction_data.fund_id
            ).first()
            
            if holding:
                # 如果已有持仓，增加份额
                holding.shares += transaction_data.shares
            else:
                # 如果没有持仓，创建新的持仓记录
                holding = UserHolding(
                    user_id=user_id,
                    fund_id=transaction_data.fund_id,
                    shares=transaction_data.shares,
                    purchase_price=fund.latest_nav
                )
                db.add(holding)
        elif transaction_data.transaction_type == "sell":
            # 检查持仓是否足够
            holding = db.query(UserHolding).filter(
                UserHolding.user_id == user_id, 
                UserHolding.fund_id == transaction_data.fund_id
            ).first()
            
            if not holding or holding.shares < transaction_data.shares:
                raise HTTPException(status_code=400, detail="Insufficient shares")
            
            # 减少持仓份额
            holding.shares -= transaction_data.shares
            
            # 如果持仓份额为0，删除持仓记录
            if holding.shares == 0:
                db.delete(holding)
            
            # 增加余额
            user.balance += transaction_amount
        else:
            raise HTTPException(status_code=400, detail="Invalid transaction type")
        
        # 创建交易记录
        transaction = Transaction(
            user_id=user_id,
            fund_id=transaction_data.fund_id,
            shares=transaction_data.shares,
            transaction_price=fund.latest_nav,
            transaction_type=transaction_data.transaction_type,
            transaction_date=datetime.now(),
            status="completed",
            amount=transaction_amount,  # 添加amount字段
            transaction_mode="one-time",  # 添加transaction_mode字段
            fee=0.0,  # 添加fee字段，默认为0
            unit_price=fund.latest_nav,  # 添加unit_price字段
            net_amount=transaction_amount  # 添加net_amount字段
        )
        db.add(transaction)
        
        # 提交事务
        db.commit()
        db.refresh(transaction)
        
        return transaction
    except Exception as e:
        # 发生异常时回滚事务
        db.rollback()
        # 如果是我们主动抛出的HTTPException，重新抛出
        if isinstance(e, HTTPException):
            raise
        # 其他异常转为500错误
        raise HTTPException(status_code=500, detail=f"Failed to create transaction: {str(e)}")

# 认证依赖项
def get_current_user(session_id: str = Header(None), db: Session = Depends(get_db)):
    """获取当前登录用户"""
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    # 从缓存获取会话数据
    session_data = cache.get(f"session:{session_id}")
    if not session_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid"
        )
    
    # 检查会话是否过期
    expires_at = datetime.fromisoformat(session_data["expires_at"])
    if expires_at < datetime.utcnow():
        cache.delete(f"session:{session_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired"
        )
    
    # 获取用户信息
    user = db.query(User).filter(User.id == session_data["user_id"]).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

# API端点
@app.post("/users/register", response_model=UserResponse)
def api_register_user(user_data: UserRegisterRequest, db: Session = Depends(get_db)):
    """用户注册API"""
    return register_user(user_data, db)

@app.post("/setup_test_user", response_model=UserResponse)
def setup_test_user(db: Session = Depends(get_db)):
    """创建测试用户，便于前端开发和测试"""
    test_username = "testuser"
    test_email = "test@example.com"
    test_password = "Test123456"
    
    # 检查测试用户是否已存在
    existing_user = db.query(User).filter(User.username == test_username).first()
    if existing_user:
        return UserResponse.from_orm(existing_user)
    
    # 创建测试用户
    hashed_password = hash_password(test_password)
    db_user = User(
        id=str(uuid.uuid4()),
        username=test_username,
        email=test_email,
        password_hash=hashed_password,
        phone=None,
        balance=10000.0,  # 初始余额10000元用于测试
        status=UserStatus.ACTIVE,
        user_type=UserType.INDIVIDUAL,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        last_login_at=None,
        is_verified=False
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return UserResponse.from_orm(db_user)

@app.post("/users/login")
def api_login_user(login_data: UserLoginRequest, db: Session = Depends(get_db)):
    """用户登录API"""
    return login_user(login_data, db)

@app.get("/users/{user_id}", response_model=UserResponse)
def api_get_user(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取用户信息API"""
    # 确保用户只能访问自己的信息
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource"
        )
    return get_user(user_id, db)

@app.put("/users/{user_id}", response_model=UserResponse)
def api_update_user(user_id: str, update_data: UserUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """更新用户信息API"""
    # 确保用户只能更新自己的信息
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource"
        )
    return update_user(user_id, update_data, db)

@app.post("/transactions", response_model=TransactionResponse)
def api_create_transaction(transaction_data: TransactionCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """创建交易API"""
    # 从当前认证用户获取user_id，不再需要从路径参数获取
    transaction = create_transaction(current_user.id, transaction_data, db)
    return TransactionResponse.from_orm(transaction)

@app.post("/users/balance/deposit")
def api_deposit_balance(update_data: BalanceUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """充值余额API"""
    # 从当前认证用户获取user_id，不再需要从路径参数获取
    new_balance = update_balance(current_user.id, update_data, "deposit", db)
    return {"balance": new_balance}

@app.post("/users/balance/withdraw")
def api_withdraw_balance(update_data: BalanceUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """提现余额API"""
    # 从当前认证用户获取user_id，不再需要从路径参数获取
    new_balance = update_balance(current_user.id, update_data, "withdraw", db)
    return {"balance": new_balance}

# 获取用户持仓
@app.get("/users/holdings", response_model=list[HoldingResponse])
def api_get_user_holdings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取用户持仓列表API"""
    # 从当前认证用户获取user_id，不再需要从路径参数获取
    return get_user_holdings(current_user.id, db)

# 获取用户交易记录
@app.get("/users/transactions", response_model=PaginatedTransactionsResponse)
def api_get_user_transactions(page: int = 1, per_page: int = 10, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取用户交易记录API"""
    # 从当前认证用户获取user_id，不再需要从路径参数获取
    return get_user_transactions(current_user.id, db, page, per_page)

# 获取用户持仓信息
def get_user_holdings(user_id: str, db: Session):
    """
    获取用户的基金持仓信息
    
    参数:
    - user_id: 用户ID
    - db: 数据库会话
    
    返回:
    - 用户持仓列表
    """
    try:
        # 检查用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 查询用户持仓
        holdings = db.query(UserHolding).filter(UserHolding.user_id == user_id).all()
        
        # 构建持仓响应列表
        holding_responses = []
        for holding in holdings:
            # 获取对应的基金信息
            fund = db.query(Fund).filter(Fund.id == holding.fund_id).first()
            if fund:
                # 计算持仓市值
                market_value = holding.shares * fund.latest_nav
                
                # 计算盈亏
                profit_loss = (fund.latest_nav - holding.purchase_price) * holding.shares
                profit_loss_rate = ((fund.latest_nav - holding.purchase_price) / holding.purchase_price) * 100 if holding.purchase_price > 0 else 0
                
                holding_responses.append({
                    "fund_id": holding.fund_id,
                    "fund_code": fund.code,
                    "fund_name": fund.name,
                    "shares": holding.shares,
                    "purchase_price": holding.purchase_price,
                    "current_nav": fund.latest_nav,
                    "market_value": market_value,
                    "profit_loss": profit_loss,
                    "profit_loss_rate": profit_loss_rate
                })
        
        # 如果没有持仓数据，返回模拟数据以便前端开发
        if not holding_responses:
            return [
                {
                    "fund_id": "mock_fund_1",
                    "fund_code": "000001",
                    "fund_name": "绿色能源主题基金",
                    "shares": 1000.0,
                    "purchase_price": 1.5,
                    "current_nav": 1.65,
                    "market_value": 1650.0,
                    "profit_loss": 150.0,
                    "profit_loss_rate": 10.0
                },
                {
                    "fund_id": "mock_fund_2",
                    "fund_code": "000002",
                    "fund_name": "环保ETF联接",
                    "shares": 500.0,
                    "purchase_price": 2.2,
                    "current_nav": 2.15,
                    "market_value": 1075.0,
                    "profit_loss": -25.0,
                    "profit_loss_rate": -2.27
                }
            ]
        
        return holding_responses
    except Exception as e:
        # 处理异常
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Failed to get user holdings: {str(e)}")

# 获取用户交易记录
def get_user_transactions(user_id: str, db: Session, page: int = 1, per_page: int = 10):
    """
    获取用户的交易记录，支持分页
    
    参数:
    - user_id: 用户ID
    - db: 数据库会话
    - page: 当前页码，默认为1
    - per_page: 每页记录数，默认为10
    
    返回:
    - 分页的交易记录列表
    """
    try:
        # 检查用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # 计算偏移量
        offset = (page - 1) * per_page
        
        # 查询总记录数
        total = db.query(Transaction).filter(Transaction.user_id == user_id).count()
        
        # 查询分页的交易记录，按交易日期降序排序
        transactions = db.query(Transaction).filter(Transaction.user_id == user_id)
        transactions = transactions.order_by(Transaction.transaction_date.desc())
        transactions = transactions.offset(offset).limit(per_page).all()
        
        # 构建交易记录响应列表
        transaction_responses = []
        for transaction in transactions:
            # 获取对应的基金信息
            fund = db.query(Fund).filter(Fund.id == transaction.fund_id).first()
            
            transaction_responses.append({
                "id": transaction.id,
                "fund_id": transaction.fund_id,
                "fund_code": fund.code if fund else None,
                "fund_name": fund.name if fund else None,
                "shares": transaction.shares,
                "transaction_price": transaction.transaction_price,
                "transaction_type": transaction.transaction_type,
                "transaction_date": transaction.transaction_date,
                "status": transaction.status,
                "amount": transaction.shares * transaction.transaction_price
            })
        
        # 如果没有交易记录，返回模拟数据以便前端开发
        if not transaction_responses and page == 1:
            mock_transactions = [
                {
                    "id": "mock_trans_1",
                    "fund_id": "mock_fund_1",
                    "fund_code": "000001",
                    "fund_name": "绿色能源主题基金",
                    "shares": 1000.0,
                    "transaction_price": 1.5,
                    "transaction_type": "buy",
                    "transaction_date": datetime.now() - timedelta(days=5),
                    "status": "completed",
                    "amount": 1500.0
                },
                {
                    "id": "mock_trans_2",
                    "fund_id": "mock_fund_2",
                    "fund_code": "000002",
                    "fund_name": "环保ETF联接",
                    "shares": 500.0,
                    "transaction_price": 2.2,
                    "transaction_type": "buy",
                    "transaction_date": datetime.now() - timedelta(days=10),
                    "status": "completed",
                    "amount": 1100.0
                }
            ]
            
            return {
                "transactions": mock_transactions,
                "page": page,
                "per_page": per_page,
                "total": 2,
                "total_pages": 1
            }
        
        # 构建分页响应
        return {
            "transactions": transaction_responses,
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": (total + per_page - 1) // per_page
        }
    except Exception as e:
        # 处理异常
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Failed to get user transactions: {str(e)}")