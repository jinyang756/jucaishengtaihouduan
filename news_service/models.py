from sqlalchemy import Column, String, Text, DateTime, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from database.database import Base

class News(Base):
    __tablename__ = "news"
    
    id = Column(String(36), primary_key=True)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    source = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False, unique=True)
    published_at = Column(DateTime, nullable=False)
    crawled_at = Column(DateTime, default=datetime.utcnow)
    language = Column(String(20), default="zh")
    country = Column(String(50))
    keywords = Column(JSON)
    categories = Column(JSON)
    is_processed = Column(Boolean, default=False)
    sentiment_score = Column(Float)
    impact_coefficient = Column(Float)