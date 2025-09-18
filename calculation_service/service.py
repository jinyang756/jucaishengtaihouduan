from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from .models import CalculationLog, NewsImpact
from .schemas import (
    CalculateNetValueRequest, CalculateNetValueResponse,
    HistoricalNetValueRequest, HistoricalNetValueResponse,
    HistoricalNetValueItem,
    NewsImpactRequest, NewsImpactResponse
)
from database.database import get_db
from common.cache import redis_client
import uuid
import numpy as np
from datetime import datetime, timedelta
import requests
import json
from fastapi import HTTPException, Depends

# 核心计算函数
def calculate_impact_coefficient(news_data, fund_id):
    """计算新闻对基金的影响系数"""
    if not news_data or 'sentiment_score' not in news_data:
        return 1.0
    
    # 情感得分
    sentiment_score = news_data['sentiment_score']
    
    # 计算重要性权重（这里简化实现）
    # 基于发布时间的权重 - 越新的新闻权重越高
    published_at = datetime.fromisoformat(news_data['published_at'].replace('Z', '+00:00'))
    time_diff_hours = (datetime.utcnow() - published_at).total_seconds() / 3600
    time_weight = max(0.1, 1.0 - (time_diff_hours / (24 * 7)))  # 一周内的新闻权重递减
    
    # 基于来源的权重
    source_reliability = {
        'xinhua': 0.9,
        'people': 0.85,
        'cnn': 0.8,
        'reuters': 0.85,
        'bbc': 0.8,
        'bloomberg': 0.85
    }
    source = news_data['source'].lower()
    source_weight = source_reliability.get(source, 0.7)
    
    # 关联性乘数（基于关键词匹配，这里简化实现）
    relevance_multiplier = 1.0
    if 'keywords' in news_data and news_data['keywords']:
        # 假设我们有一个基金相关关键词的缓存
        cache_key = f"fund_keywords:{fund_id}"
        fund_keywords = redis_client.get(cache_key)
        if fund_keywords:
            fund_keywords = set(fund_keywords.decode('utf-8').split(','))
            news_keywords = set(news_data['keywords'])
            common_keywords = fund_keywords.intersection(news_keywords)
            relevance_multiplier = 1.0 + (0.1 * len(common_keywords))
    
    # 计算最终影响系数
    # 将情感得分映射到0.5-1.5范围
    base_impact = 0.5 + (sentiment_score + 1.0) * 0.5
    final_impact = base_impact * time_weight * source_weight * relevance_multiplier
    
    # 限制在0.1-2.0范围内
    final_impact = max(0.1, min(2.0, final_impact))
    
    return final_impact

def calculate_fund_net_value(fund_id, date=None, include_news_impact=True, params=None, db=None):
    """计算基金净值"""
    if date is None:
        date = datetime.utcnow()
    
    # 从缓存或数据库获取基金的最新净值
    cache_key = f"fund_latest:{fund_id}"
    latest_fund_data = redis_client.get(cache_key)
    
    if latest_fund_data:
        latest_fund_data = json.loads(latest_fund_data)
        previous_net_value = latest_fund_data.get('net_value', 1.0)
    else:
        # 这里简化处理，实际应该从数据库查询
        previous_net_value = 1.0  # 默认初始净值
    
    # 计算基础变化率（这里简化实现，实际应基于资产配置和市场数据）
    base_change_rate = 0.001  # 假设每日基础变化率为0.1%
    
    # 计算新闻影响
    news_impact_coefficient = 1.0
    news_impact_count = 0
    
    if include_news_impact:
        # 获取最近24小时内与该基金相关的新闻
        try:
            # 假设我们通过API调用来获取相关新闻
            news_response = requests.get(f"http://localhost:8001/news/latest?fund_id={fund_id}&hours=24")
            if news_response.status_code == 200:
                news_items = news_response.json()
                
                # 计算每条新闻的影响系数并取平均值
                if news_items:
                    impact_coefficients = []
                    for news in news_items:
                        impact_coefficient = calculate_impact_coefficient(news, fund_id)
                        impact_coefficients.append(impact_coefficient)
                        
                        # 记录新闻影响
                        if db:
                            news_impact = NewsImpact(
                                id=str(uuid.uuid4()),
                                news_id=news['id'],
                                fund_id=fund_id,
                                impact_coefficient=impact_coefficient,
                                factors={
                                    'sentiment_score': news.get('sentiment_score', 0),
                                    'source': news.get('source', ''),
                                    'published_at': news.get('published_at', '')
                                },
                                source_news_impact=news.get('impact_coefficient', 0)
                            )
                            db.add(news_impact)
                    
                    news_impact_coefficient = np.mean(impact_coefficients)
                    news_impact_count = len(news_items)
        except Exception as e:
            print(f"Error fetching news: {e}")
    
    # 计算调整因子（简化实现）
    adjustment_factor = 1.0
    if params and 'adjustment' in params:
        adjustment_factor = 1.0 + params['adjustment']
    
    # 计算最终净值
    net_value = previous_net_value * (1 + base_change_rate) * news_impact_coefficient * adjustment_factor
    
    # 应用净值限制（防止异常波动）
    max_daily_change = 0.1  # 每日最大变化10%
    min_net_value = previous_net_value * (1 - max_daily_change)
    max_net_value = previous_net_value * (1 + max_daily_change)
    net_value = max(min_net_value, min(max_net_value, net_value))
    
    # 计算变化百分比
    change_percentage = ((net_value - previous_net_value) / previous_net_value) * 100
    
    return {
        'net_value': round(net_value, 4),
        'previous_net_value': previous_net_value,
        'change_percentage': round(change_percentage, 2),
        'news_impact_count': news_impact_count
    }

# 基金净值计算函数
def calculate_net_value(request: CalculateNetValueRequest, db: Session = Depends(get_db)):
    """计算基金净值"""
    try:
        # 执行净值计算
        result = calculate_fund_net_value(
            request.fund_id,
            request.date,
            request.include_news_impact,
            request.parameters,
            db
        )
        
        # 创建计算日志
        log = CalculationLog(
            id=str(uuid.uuid4()),
            fund_id=request.fund_id,
            input_params={
                'date': request.date.isoformat() if request.date else None,
                'include_news_impact': request.include_news_impact,
                'parameters': request.parameters
            },
            result=result['net_value'],
            status="success"
        )
        db.add(log)
        db.commit()
        
        # 更新缓存
        cache_key = f"fund_latest:{request.fund_id}"
        redis_client.set(cache_key, json.dumps({
            'fund_id': request.fund_id,
            'net_value': result['net_value'],
            'calculation_time': datetime.utcnow().isoformat()
        }))
        
        return CalculateNetValueResponse(
            fund_id=request.fund_id,
            date=request.date or datetime.utcnow(),
            net_value=result['net_value'],
            previous_net_value=result['previous_net_value'],
            change_percentage=result['change_percentage'],
            calculation_time=datetime.utcnow(),
            news_impact_count=result['news_impact_count']
        )
    except Exception as e:
        # 记录错误日志
        log = CalculationLog(
            id=str(uuid.uuid4()),
            fund_id=request.fund_id,
            input_params={
                'date': request.date.isoformat() if request.date else None,
                'include_news_impact': request.include_news_impact,
                'parameters': request.parameters
            },
            status="error",
            error_message=str(e)
        )
        db.add(log)
        db.commit()
        
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calculate/historical", response_model=HistoricalNetValueResponse)
def get_historical_net_value(request: HistoricalNetValueRequest, db: Session = Depends(get_db)):
    """获取基金历史净值数据"""
    # 验证日期范围
    if request.start_date > request.end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    
    # 生成日期列表（简化实现）
    dates = []
    current_date = request.start_date
    delta = {
        'daily': timedelta(days=1),
        'weekly': timedelta(weeks=1),
        'monthly': timedelta(days=30)  # 简化处理，实际应考虑月份天数差异
    }[request.frequency]
    
    while current_date <= request.end_date:
        dates.append(current_date)
        current_date += delta
    
    # 为每个日期计算净值（这里简化实现，实际应该从数据库查询历史数据）
    data = []
    previous_value = 1.0  # 假设初始净值为1.0
    
    for date in dates:
        # 模拟净值计算
        # 在实际应用中，这里应该查询数据库中的历史净值数据
        # 为了演示，我们生成随机变化
        random_change = np.random.normal(0.001, 0.005)
        net_value = previous_value * (1 + random_change)
        change_percentage = ((net_value - previous_value) / previous_value) * 100 if previous_value else 0
        
        data.append(HistoricalNetValueItem(
            date=date,
            net_value=round(net_value, 4),
            change_percentage=round(change_percentage, 2)
        ))
        
        previous_value = net_value
    
    return HistoricalNetValueResponse(
        fund_id=request.fund_id,
        data=data,
        total_items=len(data)
    )

@app.post("/calculate/news_impact", response_model=NewsImpactResponse)
def calculate_news_impact(request: NewsImpactRequest, db: Session = Depends(get_db)):
    """评估新闻对基金的影响"""
    try:
        # 从新闻服务获取新闻详情
        news_response = requests.get(f"http://localhost:8001/news/{request.news_id}")
        if news_response.status_code != 200:
            raise HTTPException(status_code=404, detail="News not found")
        
        news_data = news_response.json()
        
        # 计算影响系数
        impact_coefficient = calculate_impact_coefficient(news_data, request.fund_id)
        
        # 保存计算结果
        news_impact = NewsImpact(
            id=str(uuid.uuid4()),
            news_id=request.news_id,
            fund_id=request.fund_id,
            impact_coefficient=impact_coefficient,
            factors={
                'sentiment_score': news_data.get('sentiment_score', 0),
                'source': news_data.get('source', ''),
                'published_at': news_data.get('published_at', '')
            },
            source_news_impact=news_data.get('impact_coefficient', 0)
        )
        db.add(news_impact)
        db.commit()
        
        return NewsImpactResponse(
            news_id=request.news_id,
            fund_id=request.fund_id,
            impact_coefficient=impact_coefficient,
            calculated_at=datetime.utcnow(),
            factors=news_impact.factors,
            source_news_impact=news_impact.source_news_impact
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calculate/batch")
def batch_calculate_net_value(fund_ids: list, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """批量计算基金净值"""
    for fund_id in fund_ids:
        background_tasks.add_task(_batch_calculate_task, fund_id, db)
    
    return {"message": f"Batch calculation started for {len(fund_ids)} funds"}

def _batch_calculate_task(fund_id: str, db: Session):
    """后台批量计算任务"""
    try:
        calculate_net_value(
            CalculateNetValueRequest(fund_id=fund_id),
            db
        )
    except Exception as e:
        print(f"Batch calculation error for fund {fund_id}: {e}")