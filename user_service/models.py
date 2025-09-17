from sqlalchemy import Column, String, Float, DateTime, Boolean, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from database.database import Base
import enum

# 用户状态枚举
class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"

# 用户类型枚举
class UserType(str, enum.Enum):
    INDIVIDUAL = "individual"
    INSTITUTION = "institution"

# 用户表模型
class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20))
    user_type = Column(Enum(UserType), default=UserType.INDIVIDUAL)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    balance = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime)
    is_verified = Column(Boolean, default=False)

# 用户持仓表模型
class UserHolding(Base):
    __tablename__ = "user_holdings"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), index=True, nullable=False)
    fund_id = Column(String(36), index=True, nullable=False)
    shares = Column(Float, default=0.0)
    purchase_cost = Column(Float, default=0.0)
    current_value = Column(Float, default=0.0)
    profit_loss = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# 交易表模型
class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(String(36), index=True, nullable=False)
    fund_id = Column(String(36), index=True, nullable=False)
    transaction_type = Column(String(20), nullable=False)  # buy, sell, dividend, etc.
    amount = Column(Float, nullable=False)
    shares = Column(Float)
    unit_price = Column(Float)
    fee = Column(Float, default=0.0)
    net_amount = Column(Float)
    status = Column(String(20), default="pending")  # pending, completed, failed
    transaction_mode = Column(String(20))  # one-time, regular, profit_taking, stop_loss
    scheduled_date = Column(DateTime)  # 用于定期定额等交易模式
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime)