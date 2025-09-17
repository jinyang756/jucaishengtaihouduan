from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from .models import RuleStatus, RuleType

class RuleBase(BaseModel):
    fund_type: str = Field(..., max_length=50)
    name: str = Field(..., max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    rule_type: RuleType
    content: dict
    priority: Optional[int] = Field(5, ge=1, le=10)

class RuleCreate(RuleBase):
    pass

class RuleUpdate(RuleBase):
    status: Optional[RuleStatus] = None

class RuleResponse(RuleBase):
    id: str
    status: RuleStatus
    created_at: datetime
    updated_at: datetime
    version: str
    
    class Config:
        orm_mode = True