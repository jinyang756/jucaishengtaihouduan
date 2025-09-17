from fastapi import FastAPI, Depends, HTTPException, status, Header
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

app = FastAPI(
    title="用户服务",
    description="绿色生态基金虚拟净值模拟系统的用户服务",
    version="1.0.0"
)

# 密码加密函数
def hash_password(password: str) -> str:
    """简单的密码哈希实现（生产环境应使用更安全的方式）"""
    # 为了简单起见，这里使用sha256哈希，实际项目应使用更安全的加密方式
    return hashlib.sha256(password.encode()).hexdigest()

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
    if user.password_hash != hash_password(login_data.password):
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
    
    # 生成会话ID（简化实现，实际项目应使用JWT）
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
def update_balance(user_id: str, update_data: BalanceUpdateRequest, action: str, db: Session) -> float:
    """更新用户余额"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if action == "deposit":
        user.balance += update_data.amount
    elif action == "withdraw":
        if user.balance < update_data.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient balance"
            )
        user.balance -= update_data.amount
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action"
        )
    
    db.commit()
    return user.balance

# 获取用户持仓
def get_user_holdings(user_id: str, db: Session) -> list:
    """获取用户持仓列表"""
    holdings = db.query(UserHolding).filter(UserHolding.user_id == user_id).all()
    return [HoldingResponse.from_orm(holding) for holding in holdings]

# 获取用户交易记录
def get_user_transactions(user_id: str, db: Session, page: int = 1, per_page: int = 10) -> PaginatedTransactionsResponse:
    """获取用户交易记录"""
    skip = (page - 1) * per_page
    
    # 查询总记录数
    total = db.query(Transaction).filter(Transaction.user_id == user_id).count()
    
    # 查询分页记录
    transactions = db.query(Transaction).filter(Transaction.user_id == user_id).order_by(Transaction.created_at.desc()).offset(skip).limit(per_page).all()
    
    return PaginatedTransactionsResponse(
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page,
        transactions=[TransactionResponse.from_orm(t) for t in transactions]
    )

# 创建交易
def create_transaction(transaction_data: TransactionRequest, user_id: str, db: Session) -> TransactionResponse:
    """创建交易"""
    try:
        # 检查用户是否存在
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # 模拟获取基金当前净值（实际应从基金服务获取）
        # 简化实现，假设所有基金当前净值为1.0
        unit_price = 1.0
        
        # 计算手续费（简化实现，统一为交易金额的0.5%）
        fee_rate = 0.005  # 0.5%
        fee = transaction_data.amount * fee_rate
        
        if transaction_data.transaction_type == "buy":
            # 买入交易
            # 检查余额是否充足
            if user.balance < transaction_data.amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient balance"
                )
            
            # 计算份额
            shares = (transaction_data.amount - fee) / unit_price
            
            # 创建交易记录
            transaction = Transaction(
                id=str(uuid.uuid4()),
                user_id=user_id,
                fund_id=transaction_data.fund_id,
                transaction_type="buy",
                amount=transaction_data.amount,
                shares=shares,
                unit_price=unit_price,
                fee=fee,
                net_amount=transaction_data.amount - fee,
                status="completed",
                transaction_mode=transaction_data.transaction_mode,
                scheduled_date=transaction_data.scheduled_date,
                completed_at=datetime.utcnow()
            )
            
            # 扣减用户余额
            user.balance -= transaction_data.amount
            
            # 更新或创建持仓记录
            holding = db.query(UserHolding).filter(
                UserHolding.user_id == user_id,
                UserHolding.fund_id == transaction_data.fund_id
            ).first()
            
            if holding:
                # 已有持仓，更新份额
                total_shares = holding.shares + shares
                holding.purchase_cost = (holding.shares * holding.purchase_cost + shares * unit_price) / total_shares
                holding.shares = total_shares
                holding.current_value = total_shares * unit_price
                holding.profit_loss = holding.current_value - (holding.shares * holding.purchase_cost)
            else:
                # 新建持仓
                holding = UserHolding(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    fund_id=transaction_data.fund_id,
                    shares=shares,
                    purchase_cost=unit_price,
                    current_value=shares * unit_price,
                    profit_loss=0.0
                )
                db.add(holding)
                
        elif transaction_data.transaction_type == "sell":
            # 卖出交易
            # 检查持仓是否存在且份额充足
            holding = db.query(UserHolding).filter(
                UserHolding.user_id == user_id,
                UserHolding.fund_id == transaction_data.fund_id
            ).first()
            
            if not holding or holding.shares < transaction_data.amount:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Insufficient shares"
                )
            
            # 计算卖出份额对应的金额
            sell_amount = transaction_data.amount * unit_price
            fee = sell_amount * fee_rate
            net_amount = sell_amount - fee
            
            # 创建交易记录
            transaction = Transaction(
                id=str(uuid.uuid4()),
                user_id=user_id,
                fund_id=transaction_data.fund_id,
                transaction_type="sell",
                amount=sell_amount,
                shares=transaction_data.amount,
                unit_price=unit_price,
                fee=fee,
                net_amount=net_amount,
                status="completed",
                transaction_mode=transaction_data.transaction_mode,
                scheduled_date=transaction_data.scheduled_date,
                completed_at=datetime.utcnow()
            )
            
            # 更新用户余额
            user.balance += net_amount
            
            # 更新持仓
            holding.shares -= transaction_data.amount
            if holding.shares == 0:
                # 持仓为0，删除持仓记录
                db.delete(holding)
            else:
                # 更新持仓价值和盈亏
                holding.current_value = holding.shares * unit_price
                holding.profit_loss = holding.current_value - (holding.shares * holding.purchase_cost)
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        return TransactionResponse.from_orm(transaction)
    except HTTPException:
        # 已定义的HTTP异常直接抛出
        raise
    except Exception as e:
        # 其他异常回滚事务
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transaction failed: {str(e)}"
        )

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
def api_deposit_balance(user_id: str, update_data: BalanceUpdateRequest, db: Session = Depends(get_db)):
    """充值余额API"""
    new_balance = update_balance(user_id, update_data, "deposit", db)
    return {"balance": new_balance}

@app.post("/users/{user_id}/balance/withdraw")
def api_withdraw_balance(user_id: str, update_data: BalanceUpdateRequest, db: Session = Depends(get_db)):
    """提现余额API"""
    new_balance = update_balance(user_id, update_data, "withdraw", db)
    return {"balance": new_balance}
# 获取用户持仓
@app.get("/users/{user_id}/holdings", response_model=list[HoldingResponse])
def api_get_user_holdings(user_id: str, db: Session = Depends(get_db)):
    """获取用户持仓列表API"""
    return get_user_holdings(user_id, db)

# 获取用户交易记录
@app.get("/users/{user_id}/transactions", response_model=PaginatedTransactionsResponse)
def api_get_user_transactions(user_id: str, page: int = 1, per_page: int = 10, db: Session = Depends(get_db)):
    """获取用户交易记录API"""
    return get_user_transactions(user_id, db, page, per_page)

@app.post("/transactions", response_model=TransactionResponse)
def api_create_transaction(
    transaction_data: TransactionRequest, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建交易API"""
    return create_transaction(transaction_data, current_user.id, db)