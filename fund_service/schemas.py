from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from .models import FundType, RiskLevel, FundStatus

class FundBase(BaseModel):
    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=100)
    fund_type: FundType
    manager: Optional[str] = Field(None, max_length=50)
    management_fee: Optional[float] = Field(0.0, ge=0.0, le=5.0)
    risk_level: Optional[RiskLevel] = RiskLevel.MEDIUM
    description: Optional[str] = Field(None, max_length=1000)
    investment_strategy: Optional[str] = Field(None, max_length=1000)
    asset_allocation: Optional[Dict] = None

class FundCreate(FundBase):
    pass

class FundUpdate(FundBase):
    status: Optional[FundStatus] = None
    launch_date: Optional[datetime] = None

class FundResponse(FundBase):
    id: str
    status: FundStatus
    launch_date: Optional[datetime] = None
    latest_nav: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class FundNetValueBase(BaseModel):
    date: datetime
    net_value: float = Field(..., ge=0.0)
    accumulated_net_value: float = Field(..., ge=0.0)
    daily_growth_rate: Optional[float] = None
    weekly_growth_rate: Optional[float] = None
    monthly_growth_rate: Optional[float] = None
    quarterly_growth_rate: Optional[float] = None
    yearly_growth_rate: Optional[float] = None

class FundNetValueCreate(FundNetValueBase):
    fund_id: str = Field(..., max_length=36)

class FundNetValueResponse(FundNetValueBase):
    id: str
    fund_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True

class FundSearchRequest(BaseModel):
    fund_type: Optional[FundType] = None
    status: Optional[FundStatus] = FundStatus.ACTIVE
    risk_level: Optional[RiskLevel] = None
    name_contains: Optional[str] = None
    min_nav: Optional[float] = None
    max_nav: Optional[float] = None

class FundPerformanceResponse(BaseModel):
    fund_id: str
    fund_name: str
    fund_code: str
    latest_nav: float
    daily_growth_rate: Optional[float] = None
    weekly_growth_rate: Optional[float] = None
    monthly_growth_rate: Optional[float] = None
    quarterly_growth_rate: Optional[float] = None
    yearly_growth_rate: Optional[float] = None
    year_to_date_growth: Optional[float] = None
    creation_date: datetime
    performance_rank: Optional[int] = None