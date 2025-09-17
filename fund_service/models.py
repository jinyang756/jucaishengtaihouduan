from sqlalchemy import Column, String, Float, DateTime, Boolean, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from database.database import Base
import enum

class FundType(str, enum.Enum):
    GREEN_ENERGY = "green_energy"
    ENVIRONMENTAL_PROTECTION = "environmental_protection"
    CLIMATE_CHANGE = "climate_change"
    SUSTAINABLE_DEVELOPMENT = "sustainable_development"
    ESG = "esg"

class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM_LOW = "medium_low"
    MEDIUM = "medium"
    MEDIUM_HIGH = "medium_high"
    HIGH = "high"

class FundStatus(str, enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    LAUNCHING = "launching"
    SUSPENDED = "suspended"

class Fund(Base):
    __tablename__ = "funds"
    
    id = Column(String(36), primary_key=True)
    code = Column(String(20), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    fund_type = Column(Enum(FundType), nullable=False)
    manager = Column(String(50))
    management_fee = Column(Float, default=0.0)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.MEDIUM)
    status = Column(Enum(FundStatus), default=FundStatus.ACTIVE)
    launch_date = Column(DateTime)
    description = Column(String(1000))
    investment_strategy = Column(String(1000))
    asset_allocation = Column(JSON)
    latest_nav = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class FundNetValue(Base):
    __tablename__ = "fund_net_values"
    
    id = Column(String(36), primary_key=True)
    fund_id = Column(String(36), nullable=False)
    date = Column(DateTime, nullable=False)
    net_value = Column(Float, nullable=False)
    accumulated_net_value = Column(Float, nullable=False)
    daily_growth_rate = Column(Float)
    weekly_growth_rate = Column(Float)
    monthly_growth_rate = Column(Float)
    quarterly_growth_rate = Column(Float)
    yearly_growth_rate = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)