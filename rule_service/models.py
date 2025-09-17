from sqlalchemy import Column, String, JSON, Enum, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
import enum
from datetime import datetime
from database.database import Base

class RuleStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DEPRECATED = "deprecated"

class RuleType(str, enum.Enum):
    KEYWORD = "keyword"
    SENTIMENT = "sentiment"
    IMPACT = "impact"
    ALLOCATION = "allocation"
    EVALUATION = "evaluation"

class Rule(Base):
    __tablename__ = "rules"
    
    id = Column(String(36), primary_key=True)
    fund_type = Column(String(50), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    rule_type = Column(Enum(RuleType), nullable=False)
    content = Column(JSON, nullable=False)
    status = Column(Enum(RuleStatus), default=RuleStatus.DRAFT)
    priority = Column(Integer, default=5)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    version = Column(String(20), default="1.0")