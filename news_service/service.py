from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from .models import News
from .schemas import NewsCreate, NewsUpdate, NewsResponse, NewsCrawlRequest
from database.database import get_db
import uuid
import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime, timedelta
import re
from textblob import TextBlob
from common.cache import redis_client
from fastapi import HTTPException, Depends

# 爬虫相关函数
def crawl_rss_feed(feed_url):
    """爬取RSS订阅源"""
    try:
        feed = feedparser.parse(feed_url)
        articles = []
        
        for entry in feed.entries:
            article = {
                'title': entry.get('title', ''),
                'content': entry.get('description', ''),
                'source': feed.feed.get('title', 'Unknown'),
                'url': entry.get('link', ''),
                'published_at': datetime(*entry.get('published_parsed', datetime.now().timetuple())[:6]) if 'published_parsed' in entry else datetime.now()
            }
            articles.append(article)
        
        return articles
    except Exception as e:
        print(f"RSS feed error: {e}")
        return []

def crawl_html_page(url):
    """爬取HTML网页"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取标题
        title = soup.find('h1').get_text().strip() if soup.find('h1') else 'Untitled'
        
        # 提取内容（简单示例，实际需要针对不同网站定制）
        paragraphs = soup.find_all('p')
        content = '\n'.join([p.get_text().strip() for p in paragraphs])
        
        # 尝试提取发布时间
        published_at = datetime.now()
        time_elements = soup.find_all(['time', 'span', 'div'], class_=re.compile(r'time|date', re.IGNORECASE))
        if time_elements:
            # 这里简化处理，实际应该使用更复杂的解析逻辑
            pass
        
        return {
            'title': title,
            'content': content,
            'source': url.split('/')[2],  # 简单提取域名作为来源
            'url': url,
            'published_at': published_at
        }
    except Exception as e:
        print(f"HTML crawl error: {e}")
        return None

# 新闻处理函数
def process_news(news_item: News, db: Session):
    """处理新闻，包括情感分析和影响系数计算"""
    # 提取关键词（简单实现）
    blob = TextBlob(news_item.content)
    keywords = [word.lower() for word, pos in blob.tags if pos.startswith('NN')][:10]  # 提取名词作为关键词
    
    # 情感分析
    sentiment_score = blob.sentiment.polarity
    
    # 这里简化了影响系数计算，实际应该根据规则服务的规则来计算
    impact_coefficient = min(max(sentiment_score * 0.5 + 0.5, 0.1), 1.5)  # 映射到0.1-1.5范围
    
    # 生成摘要
    summary = ' '.join(sentiment_score.sentences[:3]) if len(blob.sentences) > 3 else str(blob)
    
    # 更新新闻项
    news_item.keywords = keywords
    news_item.sentiment_score = sentiment_score
    news_item.impact_coefficient = impact_coefficient
    news_item.summary = summary
    news_item.is_processed = True
    
    db.commit()
    db.refresh(news_item)
    
    # 将处理后的新闻存入缓存
    cache_key = f"news:{news_item.id}"
    redis_client.set(cache_key, news_item.json(), ex=3600)  # 缓存1小时

# 创建新闻函数
def create_news(news: NewsCreate, db: Session):
    """创建新闻"""
    # 检查URL是否已存在
    existing_news = db.query(News).filter(News.url == news.url).first()
    if existing_news:
        return existing_news
    
    db_news = News(
        id=str(uuid.uuid4()),
        title=news.title,
        content=news.content,
        source=news.source,
        url=news.url,
        published_at=news.published_at,
        language=news.language,
        country=news.country,
        keywords=news.keywords,
        categories=news.categories
    )
    
    db.add(db_news)
    db.commit()
    db.refresh(db_news)
    return db_news

def get_news(news_id: str, db: Session):
    """获取新闻详情"""
    # 先检查缓存
    cache_key = f"news:{news_id}"
    cached_news = redis_client.get(cache_key)
    if cached_news:
        return NewsResponse.parse_raw(cached_news)
    
    news = db.query(News).filter(News.id == news_id).first()
    if not news:
        raise HTTPException(status_code=404, detail="News not found")
    
    # 存入缓存
    redis_client.set(cache_key, news.json(), ex=3600)
    return news

def update_news(news_id: str, news: NewsUpdate, db: Session):
    """更新新闻信息"""
    db_news = db.query(News).filter(News.id == news_id).first()
    if not db_news:
        raise HTTPException(status_code=404, detail="News not found")
    
    # 更新新闻字段
    for key, value in news.dict(exclude_unset=True).items():
        setattr(db_news, key, value)
    
    db.commit()
    db.refresh(db_news)
    
    # 更新缓存
    cache_key = f"news:{news_id}"
    redis_client.set(cache_key, db_news.json(), ex=3600)
    
    return db_news

def crawl_news(request: NewsCrawlRequest, background_tasks, db: Session):
    """批量爬取新闻"""
    for source in request.sources[:request.max_items]:
        background_tasks.add_task(_crawl_news_task, source, request.crawl_type, db)
    
    return {"message": f"Started crawling {len(request.sources)} sources, max {request.max_items} items each"}

def _crawl_news_task(source: str, crawl_type: str, db: Session):
    """后台爬虫任务"""
    try:
        if crawl_type == "rss":
            articles = crawl_rss_feed(source)
            for article in articles:
                # 检查是否已存在
                if not db.query(News).filter(News.url == article['url']).first():
                    db_news = News(
                        id=str(uuid.uuid4()),
                        **article
                    )
                    db.add(db_news)
            db.commit()
        elif crawl_type == "html":
            article = crawl_html_page(source)
            if article and not db.query(News).filter(News.url == article['url']).first():
                db_news = News(
                    id=str(uuid.uuid4()),
                    **article
                )
                db.add(db_news)
                db.commit()
    except Exception as e:
        print(f"Crawl task error: {e}")

@app.get("/news/latest")
def get_latest_news(limit: int = 10, hours: int = 24, db: Session = Depends(get_db)):
    """获取最新新闻"""
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    news = db.query(News).filter(News.published_at >= cutoff_time).order_by(News.published_at.desc()).limit(limit).all()
    return news