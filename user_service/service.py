from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .models import User, UserHolding, Transaction, UserStatus
from .schemas import (
    UserRegisterRequest, UserLoginRequest, UserResponse, 
    UserUpdateRequest, BalanceUpdateRequest, HoldingResponse,
    TransactionRequest, TransactionResponse, PaginatedTransactionsResponse
)
from database.database import get_db
from common.cache import cache
import uuid
import hashlib
import json
from datetime import datetime, timedelta
import secrets
from starlette import status
# 添加passlib和bcrypt用于密码哈希
from passlib.context import CryptContext
import re
import logging

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
        transaction_amount = transaction_data.shares * fund.nav
        
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
                    purchase_price=fund.nav
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
            transaction_price=fund.nav,
            transaction_type=transaction_data.transaction_type,
            transaction_date=datetime.datetime.now(),
            status="completed"
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

@app.post("/users/{user_id}/balance/deposit")
def api_deposit_balance(user_id: str, update_data: BalanceUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """充值余额API"""
    # 确保用户只能操作自己的账户
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource"
        )
    new_balance = update_balance(user_id, update_data, "deposit", db)
    return {"balance": new_balance}

@app.post("/users/{user_id}/balance/withdraw")
def api_withdraw_balance(user_id: str, update_data: BalanceUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """提现余额API"""
    # 确保用户只能操作自己的账户
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource"
        )
    new_balance = update_balance(user_id, update_data, "withdraw", db)
    return {"balance": new_balance}

# 获取用户持仓
@app.get("/users/{user_id}/holdings", response_model=list[HoldingResponse])
def api_get_user_holdings(user_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取用户持仓列表API"""
    # 确保用户只能访问自己的持仓
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource"
        )
    return get_user_holdings(user_id, db)

# 获取用户交易记录
@app.get("/users/{user_id}/transactions", response_model=PaginatedTransactionsResponse)
def api_get_user_transactions(user_id: str, page: int = 1, per_page: int = 10, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取用户交易记录API"""
    # 确保用户只能访问自己的交易记录
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this resource"
        )
    return get_user_transactions(user_id, db, page, per_page)

@app.post("/transactions", response_model=TransactionResponse)
def api_create_transaction(transaction_data: TransactionCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """创建交易API"""
    # 从当前认证用户获取user_id，不再需要从路径参数获取
    transaction = create_transaction(current_user.id, transaction_data, db)
    return TransactionResponse.from_orm(transaction)

@app.post("/users/{user_id}/balance/deposit")
def api_deposit_balance(update_data: BalanceUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """充值余额API"""
    # 从当前认证用户获取user_id，不再需要从路径参数获取
    new_balance = update_balance(current_user.id, update_data, "deposit", db)
    return {"balance": new_balance}

@app.post("/users/{user_id}/balance/withdraw")
def api_withdraw_balance(update_data: BalanceUpdateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """提现余额API"""
    # 从当前认证用户获取user_id，不再需要从路径参数获取
    new_balance = update_balance(current_user.id, update_data, "withdraw", db)
    return {"balance": new_balance}

# 获取用户持仓
@app.get("/users/{user_id}/holdings", response_model=list[HoldingResponse])
def api_get_user_holdings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取用户持仓列表API"""
    # 从当前认证用户获取user_id，不再需要从路径参数获取
    return get_user_holdings(current_user.id, db)

# 获取用户交易记录
@app.get("/users/{user_id}/transactions", response_model=PaginatedTransactionsResponse)
def api_get_user_transactions(page: int = 1, per_page: int = 10, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取用户交易记录API"""
    # 从当前认证用户获取user_id，不再需要从路径参数获取
    return get_user_transactions(current_user.id, db, page, per_page)