from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict

class CalculateNetValueRequest(BaseModel):
    fund_id: str = Field(..., max_length=36)
    date: Optional[datetime] = None
    include_news_impact: Optional[bool] = True
    parameters: Optional[Dict] = None

class CalculateNetValueResponse(BaseModel):
    fund_id: str
    date: datetime
    net_value: float
    previous_net_value: Optional[float] = None
    change_percentage: Optional[float] = None
    calculation_time: datetime
    news_impact_count: Optional[int] = 0

class HistoricalNetValueRequest(BaseModel):
    fund_id: str = Field(..., max_length=36)
    start_date: datetime
    end_date: datetime
    frequency: str = Field("daily", regex="^(daily|weekly|monthly)$")

class HistoricalNetValueItem(BaseModel):
    date: datetime
    net_value: float
    change_percentage: Optional[float] = None

class HistoricalNetValueResponse(BaseModel):
    fund_id: str
    data: List[HistoricalNetValueItem]
    total_items: int

class NewsImpactRequest(BaseModel):
    news_id: str = Field(..., max_length=36)
    fund_id: str = Field(..., max_length=36)

class NewsImpactResponse(BaseModel):
    news_id: str
    fund_id: str
    impact_coefficient: float
    calculated_at: datetime
    factors: Dict
    source_news_impact: Optional[float] = None