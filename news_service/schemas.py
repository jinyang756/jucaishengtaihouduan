from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict

class NewsBase(BaseModel):
    title: str = Field(..., max_length=255)
    content: str
    source: str = Field(..., max_length=100)
    url: str = Field(..., max_length=500)
    published_at: datetime
    language: Optional[str] = Field("zh", max_length=20)
    country: Optional[str] = Field(None, max_length=50)
    keywords: Optional[List[str]] = None
    categories: Optional[List[str]] = None

class NewsCreate(NewsBase):
    pass

class NewsUpdate(BaseModel):
    summary: Optional[str] = None
    is_processed: Optional[bool] = None
    sentiment_score: Optional[float] = None
    impact_coefficient: Optional[float] = None
    keywords: Optional[List[str]] = None
    categories: Optional[List[str]] = None

class NewsResponse(NewsBase):
    id: str
    crawled_at: datetime
    is_processed: bool
    sentiment_score: Optional[float]
    impact_coefficient: Optional[float]
    summary: Optional[str]
    
    class Config:
        orm_mode = True

class NewsCrawlRequest(BaseModel):
    sources: List[str] = Field(..., min_items=1)
    crawl_type: str = Field("rss", regex="^(rss|html|api)$")
    max_items: Optional[int] = Field(100, ge=1, le=1000)