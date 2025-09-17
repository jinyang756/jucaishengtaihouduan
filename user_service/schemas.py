from pydantic import BaseModel, EmailStr, Field, validator
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, validator, EmailStr
from enum import Enum
from .models import UserStatus, UserType

class TransactionType(str, Enum):
    BUY = "buy"
    SELL = "sell"

class TransactionCreateRequest(BaseModel):
    fund_id: str
    shares: float = Field(..., gt=0)
    transaction_type: TransactionType

    @validator('shares')
    def validate_shares(cls, v):
        if v <= 0:
            raise ValueError("Shares must be greater than 0")
        return v

# 用户注册请求模型
class UserRegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    phone: Optional[str] = None

# 用户登录请求模型
class UserLoginRequest(BaseModel):
    username: str
    password: str

# 用户响应模型
class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    phone: Optional[str]
    user_type: UserType
    status: UserStatus
    balance: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

# 用户更新请求模型
class UserUpdateRequest(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[UserStatus] = None

# 用户余额更新请求模型
class BalanceUpdateRequest(BaseModel):
    amount: float = Field(..., gt=0)
    
    @validator('amount')
    def validate_amount(cls, value):
        if value <= 0:
            raise ValueError("Amount must be positive")
        return value

# 持仓响应模型
class HoldingResponse(BaseModel):
    fund_id: str
    fund_code: str
    fund_name: str
    shares: float
    purchase_price: float
    current_nav: float
    market_value: float
    profit_loss: float
    profit_loss_rate: float

# 交易请求模型
class TransactionRequest(BaseModel):
    fund_id: str
    transaction_type: str  # buy, sell
    amount: float = Field(..., gt=0)
    transaction_mode: str = "one-time"  # one-time, regular, profit_taking, stop_loss
    scheduled_date: Optional[datetime] = None
    
    @validator('transaction_type')
    def validate_transaction_type(cls, value):
        if value not in ['buy', 'sell']:
            raise ValueError("Transaction type must be 'buy' or 'sell'")
        return value
    
    @validator('transaction_mode')
    def validate_transaction_mode(cls, value):
        valid_modes = ['one-time', 'regular', 'profit_taking', 'stop_loss']
        if value not in valid_modes:
            raise ValueError(f"Transaction mode must be one of: {', '.join(valid_modes)}")
        return value

# 交易响应模型
class TransactionResponse(BaseModel):
    id: str
    user_id: str
    fund_id: str
    transaction_type: str
    amount: float
    shares: Optional[float]
    unit_price: Optional[float]
    fee: float
    net_amount: Optional[float]
    status: str
    transaction_mode: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        orm_mode = True

# 分页交易记录响应模型
class PaginatedTransactionsResponse(BaseModel):
    total: int
    page: int
    per_page: int
    total_pages: int
    transactions: List[TransactionResponse]