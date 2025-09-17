from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from database.database import Base

class CalculationLog(Base):
    __tablename__ = "calculation_logs"
    
    id = Column(String(36), primary_key=True)
    fund_id = Column(String(36), nullable=False)
    calculation_time = Column(DateTime, default=datetime.utcnow)
    input_params = Column(JSON)
    result = Column(Float)
    status = Column(String(20), default="success")
    error_message = Column(String(500))

class NewsImpact(Base):
    __tablename__ = "news_impacts"
    
    id = Column(String(36), primary_key=True)
    news_id = Column(String(36), nullable=False)
    fund_id = Column(String(36), nullable=False)
    impact_coefficient = Column(Float, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    factors = Column(JSON)
    source_news_impact = Column(Float)