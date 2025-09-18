from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from .models import Fund, FundNetValue, FundStatus
from .schemas import (
    FundCreate, FundUpdate, FundResponse,
    FundNetValueCreate, FundNetValueResponse,
    FundSearchRequest, FundPerformanceResponse
)
from database.database import get_db
from common.cache import redis_client
import uuid
from datetime import datetime, timedelta
import json
from fastapi import HTTPException, Depends

# 基金CRUD操作
def create_fund(fund: FundCreate, db: Session):
    """创建新基金"""
    # 检查基金代码是否已存在
    existing_fund = db.query(Fund).filter(Fund.code == fund.code).first()
    if existing_fund:
        raise HTTPException(status_code=400, detail="Fund code already exists")
    
    db_fund = Fund(
        id=str(uuid.uuid4()),
        code=fund.code,
        name=fund.name,
        fund_type=fund.fund_type,
        manager=fund.manager,
        management_fee=fund.management_fee,
        risk_level=fund.risk_level,
        description=fund.description,
        investment_strategy=fund.investment_strategy,
        asset_allocation=fund.asset_allocation,
        status=FundStatus.ACTIVE,
        launch_date=datetime.utcnow()
    )
    
    db.add(db_fund)
    db.commit()
    db.refresh(db_fund)
    
    # 初始化基金净值
    initial_nav = FundNetValue(
        id=str(uuid.uuid4()),
        fund_id=db_fund.id,
        date=datetime.utcnow(),
        net_value=1.0,
        accumulated_net_value=1.0
    )
    db.add(initial_nav)
    db.commit()
    
    # 更新缓存
    cache_key = f"fund:{db_fund.id}"
    redis_client.set(cache_key, json.dumps(fund.dict()))
    
    return db_fund

@app.get("/funds/{fund_id}", response_model=FundResponse)
def get_fund(fund_id: str, db: Session = Depends(get_db)):
    """获取基金详情"""
    # 先检查缓存
    cache_key = f"fund:{fund_id}"
    cached_fund = redis_client.get(cache_key)
    if cached_fund:
        fund_data = json.loads(cached_fund)
        return FundResponse(**fund_data)
    
    fund = db.query(Fund).filter(Fund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    
    # 存入缓存
    redis_client.set(cache_key, json.dumps(fund.dict()))
    return fund

@app.put("/funds/{fund_id}", response_model=FundResponse)
def update_fund(fund_id: str, fund: FundUpdate, db: Session = Depends(get_db)):
    """更新基金信息"""
    db_fund = db.query(Fund).filter(Fund.id == fund_id).first()
    if not db_fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    
    # 更新基金字段
    for key, value in fund.dict(exclude_unset=True).items():
        setattr(db_fund, key, value)
    
    db.commit()
    db.refresh(db_fund)
    
    # 更新缓存
    cache_key = f"fund:{fund_id}"
    redis_client.set(cache_key, json.dumps(db_fund.dict()))
    
    return db_fund

@app.delete("/funds/{fund_id}")
def delete_fund(fund_id: str, db: Session = Depends(get_db)):
    """删除基金（标记为已关闭）"""
    fund = db.query(Fund).filter(Fund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    
    # 不实际删除，而是将状态设置为CLOSED
    fund.status = FundStatus.CLOSED
    db.commit()
    
    # 从缓存中删除
    cache_key = f"fund:{fund_id}"
    redis_client.delete(cache_key)
    
    return {"message": "Fund marked as closed"}

# 基金净值操作
def add_fund_net_value(fund_id: str, net_value: FundNetValueCreate, db: Session):
    """添加基金净值记录"""
    # 检查基金是否存在
    fund = db.query(Fund).filter(Fund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    
    # 检查该日期的净值记录是否已存在
    existing_nav = db.query(FundNetValue).filter(
        FundNetValue.fund_id == fund_id,
        FundNetValue.date == net_value.date
    ).first()
    if existing_nav:
        raise HTTPException(status_code=400, detail="Net value for this date already exists")
    
    db_net_value = FundNetValue(
        id=str(uuid.uuid4()),
        fund_id=fund_id,
        date=net_value.date,
        net_value=net_value.net_value,
        accumulated_net_value=net_value.accumulated_net_value,
        daily_growth_rate=net_value.daily_growth_rate,
        weekly_growth_rate=net_value.weekly_growth_rate,
        monthly_growth_rate=net_value.monthly_growth_rate,
        quarterly_growth_rate=net_value.quarterly_growth_rate,
        yearly_growth_rate=net_value.yearly_growth_rate
    )
    
    db.add(db_net_value)
    db.commit()
    db.refresh(db_net_value)
    
    # 更新基金的最新净值
    fund.latest_nav = net_value.net_value
    db.commit()
    
    # 更新缓存
    cache_key = f"fund:{fund_id}:latest_nav"
    redis_client.set(cache_key, json.dumps(db_net_value.dict()))
    
    return db_net_value

def get_latest_net_value(fund_id: str, db: Session):
    """获取基金最新净值"""
    # 先检查缓存
    cache_key = f"fund:{fund_id}:latest_nav"
    cached_nav = redis_client.get(cache_key)
    if cached_nav:
        nav_data = json.loads(cached_nav)
        return FundNetValueResponse(**nav_data)
    
    net_value = db.query(FundNetValue).filter(
        FundNetValue.fund_id == fund_id
    ).order_by(FundNetValue.date.desc()).first()
    
    if not net_value:
        raise HTTPException(status_code=404, detail="No net value data found")
    
    # 存入缓存
    redis_client.set(cache_key, json.dumps(net_value.dict()))
    return net_value

def get_fund_net_values(fund_id: str, start_date: datetime, end_date: datetime, db: Session):
    """获取基金净值历史数据"""
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    
    net_values = db.query(FundNetValue).filter(
        FundNetValue.fund_id == fund_id,
        FundNetValue.date >= start_date,
        FundNetValue.date <= end_date
    ).order_by(FundNetValue.date.asc()).all()
    
    return net_values

# 基金搜索和筛选
def search_funds(request: FundSearchRequest, db: Session, skip: int = 0, limit: int = 100):
    """搜索和筛选基金"""
    query = db.query(Fund)
    
    # 应用筛选条件
    if request.fund_type:
        query = query.filter(Fund.fund_type == request.fund_type)
    
    if request.status:
        query = query.filter(Fund.status == request.status)
    
    if request.risk_level:
        query = query.filter(Fund.risk_level == request.risk_level)
    
    if request.name_contains:
        query = query.filter(Fund.name.contains(request.name_contains))
    
    if request.min_nav is not None:
        query = query.filter(Fund.latest_nav >= request.min_nav)
    
    if request.max_nav is not None:
        query = query.filter(Fund.latest_nav <= request.max_nav)
    
    funds = query.offset(skip).limit(limit).all()
    return funds

# 基金绩效分析
@app.get("/funds/{fund_id}/performance", response_model=FundPerformanceResponse)
def get_fund_performance(fund_id: str, db: Session = Depends(get_db)):
    """获取基金绩效数据"""
    fund = db.query(Fund).filter(Fund.id == fund_id).first()
    if not fund:
        raise HTTPException(status_code=404, detail="Fund not found")
    
    # 获取最新净值数据
    latest_nav = db.query(FundNetValue).filter(
        FundNetValue.fund_id == fund_id
    ).order_by(FundNetValue.date.desc()).first()
    
    # 计算年初至今增长率
    year_start = datetime(datetime.utcnow().year, 1, 1)
    year_start_nav = db.query(FundNetValue).filter(
        FundNetValue.fund_id == fund_id,
        FundNetValue.date <= year_start
    ).order_by(FundNetValue.date.desc()).first()
    
    year_to_date_growth = None
    if latest_nav and year_start_nav:
        year_to_date_growth = ((latest_nav.net_value - year_start_nav.net_value) / year_start_nav.net_value) * 100
    
    # 构建绩效响应
    performance = FundPerformanceResponse(
        fund_id=fund.id,
        fund_name=fund.name,
        fund_code=fund.code,
        latest_nav=fund.latest_nav,
        creation_date=fund.created_at,
        year_to_date_growth=round(year_to_date_growth, 2) if year_to_date_growth is not None else None
    )
    
    # 如果有最新净值数据，补充增长率信息
    if latest_nav:
        performance.daily_growth_rate = latest_nav.daily_growth_rate
        performance.weekly_growth_rate = latest_nav.weekly_growth_rate
        performance.monthly_growth_rate = latest_nav.monthly_growth_rate
        performance.quarterly_growth_rate = latest_nav.quarterly_growth_rate
        performance.yearly_growth_rate = latest_nav.yearly_growth_rate
    
    return performance

@app.get("/funds/performance/ranking")
def get_fund_performance_ranking(period: str = "monthly", limit: int = 10, db: Session = Depends(get_db)):
    """获取基金绩效排名"""
    # 验证周期参数
    valid_periods = ["daily", "weekly", "monthly", "quarterly", "yearly", "ytd"]
    if period not in valid_periods:
        raise HTTPException(status_code=400, detail=f"Invalid period. Valid periods are: {', '.join(valid_periods)}")
    
    # 获取所有活跃基金
    active_funds = db.query(Fund).filter(Fund.status == FundStatus.ACTIVE).all()
    
    # 计算每个基金的绩效并排名
    performance_list = []
    
    for fund in active_funds:
        # 获取最新净值数据
        latest_nav = db.query(FundNetValue).filter(
            FundNetValue.fund_id == fund.id
        ).order_by(FundNetValue.date.desc()).first()
        
        if latest_nav:
            # 根据周期选择增长率
            if period == "daily":
                growth_rate = latest_nav.daily_growth_rate or 0
            elif period == "weekly":
                growth_rate = latest_nav.weekly_growth_rate or 0
            elif period == "monthly":
                growth_rate = latest_nav.monthly_growth_rate or 0
            elif period == "quarterly":
                growth_rate = latest_nav.quarterly_growth_rate or 0
            elif period == "yearly":
                growth_rate = latest_nav.yearly_growth_rate or 0
            elif period == "ytd":
                # 计算年初至今增长率
                year_start = datetime(datetime.utcnow().year, 1, 1)
                year_start_nav = db.query(FundNetValue).filter(
                    FundNetValue.fund_id == fund.id,
                    FundNetValue.date <= year_start
                ).order_by(FundNetValue.date.desc()).first()
                
                if year_start_nav and year_start_nav.net_value > 0:
                    growth_rate = ((latest_nav.net_value - year_start_nav.net_value) / year_start_nav.net_value) * 100
                else:
                    growth_rate = 0
            
            performance_list.append({
                'fund_id': fund.id,
                'fund_name': fund.name,
                'fund_code': fund.code,
                'growth_rate': growth_rate,
                'latest_nav': fund.latest_nav
            })
    
    # 按增长率降序排序
    performance_list.sort(key=lambda x: x['growth_rate'], reverse=True)
    
    # 添加排名
    for i, item in enumerate(performance_list[:limit]):
        item['performance_rank'] = i + 1
    
    return performance_list[:limit]