#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.database import Base, get_database_url
from user_service.models import User, UserHolding, Transaction
from fund_service.models import Fund, FundNetValue, FundType, RiskLevel, FundStatus

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 初始化数据库
def init_database():
    """初始化数据库，创建会话"""
    database_url = get_database_url()
    engine = create_engine(database_url)
    
    # 创建所有表
    Base.metadata.drop_all(bind=engine)  # 先删除所有表（注意：生产环境不要使用）
    Base.metadata.create_all(bind=engine)
    
    # 创建会话
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return Session()

# 创建模拟基金数据
def create_mock_funds(db):
    """创建模拟基金数据"""
    funds = [
        Fund(
            id=str(uuid.uuid4()),
            code="100001",
            name="绿色生态成长混合基金",
            fund_type=FundType.GREEN_ENERGY,
            manager="张经理",
            management_fee=1.5,
            risk_level=RiskLevel.MEDIUM,
            status=FundStatus.ACTIVE,
            launch_date=datetime(2020, 1, 1),
            description="主要投资于绿色生态相关产业的成长型股票，追求长期稳健增长。",
            investment_strategy="重点关注新能源、环保、绿色科技等领域的优质企业。",
            asset_allocation={"股票": 70, "债券": 20, "现金": 10},
            latest_nav=1.2345,
            created_at=datetime(2020, 1, 1),
            updated_at=datetime.utcnow()
        ),
        Fund(
            id=str(uuid.uuid4()),
            code="100002",
            name="低碳环保债券基金",
            fund_type=FundType.ENVIRONMENTAL_PROTECTION,
            manager="李经理",
            management_fee=0.8,
            risk_level=RiskLevel.LOW,
            status=FundStatus.ACTIVE,
            launch_date=datetime(2019, 6, 1),
            description="投资于低碳环保相关的固定收益类资产，追求稳定收益。",
            investment_strategy="投资于符合低碳环保政策的企业债券和政府债券。",
            asset_allocation={"债券": 85, "股票": 5, "现金": 10},
            latest_nav=1.0876,
            created_at=datetime(2019, 6, 1),
            updated_at=datetime.utcnow()
        ),
        Fund(
            id=str(uuid.uuid4()),
            code="100003",
            name="可持续发展指数基金",
            fund_type=FundType.SUSTAINABLE_DEVELOPMENT,
            manager="王经理",
            management_fee=0.5,
            risk_level=RiskLevel.MEDIUM_HIGH,
            status=FundStatus.ACTIVE,
            launch_date=datetime(2021, 3, 1),
            description="跟踪可持续发展相关指数的被动型基金，分散投资。",
            investment_strategy="完全复制可持续发展指数成分股，追求与指数一致的收益。",
            asset_allocation={"股票": 95, "现金": 5},
            latest_nav=1.4532,
            created_at=datetime(2021, 3, 1),
            updated_at=datetime.utcnow()
        )
    ]
    
    # 添加基金数据
    for fund in funds:
        db.add(fund)
    
    # 提交到数据库
    db.commit()
    
    # 添加基金净值数据
    for fund in funds:
        # 创建过去30天的净值数据
        for i in range(30):
            date = datetime.utcnow() - timedelta(days=i)
            # 生成一些波动的净值数据
            base_nav = fund.latest_nav
            fluctuation = (i % 5 - 2) * 0.005  # -0.01, -0.005, 0, 0.005, 0.01 的波动
            net_value = max(0.5, base_nav + fluctuation)
            
            fund_nav = FundNetValue(
                id=str(uuid.uuid4()),
                fund_id=fund.id,
                date=date,
                net_value=net_value,
                accumulated_net_value=net_value * (1 + 0.0001 * i),  # 累计净值略高一些
                daily_growth_rate=fluctuation * 100 if i > 0 else 0,
                weekly_growth_rate=(net_value - base_nav) * 100 / base_nav if i % 7 == 0 else None,
                monthly_growth_rate=(net_value - base_nav) * 100 / base_nav if i == 0 else None,
                quarterly_growth_rate=None,
                yearly_growth_rate=None,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(fund_nav)
    
    db.commit()
    
    return funds

# 创建模拟用户数据
def create_mock_users(db):
    """创建模拟用户数据"""
    users = [
        User(
            id=str(uuid.uuid4()),
            username="testuser1",
            email="testuser1@example.com",
            password_hash="$2b$12$LbRkM5iQlS9u0G6ZJ7zR0e8qK3JQeJQZ6X5W9Y8V7U6T5R4E3W",  # 密码: 12345678
            phone="13800138001",
            user_type="individual",
            status="active",
            balance=10000.0,  # 初始赠送10000元模拟资金
            created_at=datetime(2023, 1, 1),
            updated_at=datetime.utcnow(),
            last_login_at=datetime.utcnow(),
            is_verified=True
        ),
        User(
            id=str(uuid.uuid4()),
            username="testuser2",
            email="testuser2@example.com",
            password_hash="$2b$12$LbRkM5iQlS9u0G6ZJ7zR0e8qK3JQeJQZ6X5W9Y8V7U6T5R4E3W",  # 密码: 12345678
            phone="13800138002",
            user_type="individual",
            status="active",
            balance=15000.0,  # 初始赠送15000元模拟资金
            created_at=datetime(2023, 2, 1),
            updated_at=datetime.utcnow(),
            last_login_at=datetime.utcnow(),
            is_verified=True
        )
    ]
    
    # 添加用户数据
    for user in users:
        db.add(user)
    
    db.commit()
    
    return users

# 创建模拟用户持仓数据
def create_mock_holdings(db, users, funds):
    """创建模拟用户持仓数据"""
    holdings = [
        # 用户1的持仓
        UserHolding(
            id=str(uuid.uuid4()),
            user_id=users[0].id,
            fund_id=funds[0].id,
            shares=1000.0,
            purchase_price=1.2,
            purchase_cost=1200.0,
            current_value=1234.5,  # 1000 * 1.2345
            profit_loss=34.5,
            created_at=datetime(2023, 3, 1),
            updated_at=datetime.utcnow()
        ),
        UserHolding(
            id=str(uuid.uuid4()),
            user_id=users[0].id,
            fund_id=funds[1].id,
            shares=2000.0,
            purchase_price=1.05,
            purchase_cost=2100.0,
            current_value=2175.2,  # 2000 * 1.0876
            profit_loss=75.2,
            created_at=datetime(2023, 4, 1),
            updated_at=datetime.utcnow()
        ),
        # 用户2的持仓
        UserHolding(
            id=str(uuid.uuid4()),
            user_id=users[1].id,
            fund_id=funds[0].id,
            shares=1500.0,
            purchase_price=1.22,
            purchase_cost=1830.0,
            current_value=1851.75,  # 1500 * 1.2345
            profit_loss=21.75,
            created_at=datetime(2023, 3, 15),
            updated_at=datetime.utcnow()
        ),
        UserHolding(
            id=str(uuid.uuid4()),
            user_id=users[1].id,
            fund_id=funds[2].id,
            shares=800.0,
            purchase_price=1.4,
            purchase_cost=1120.0,
            current_value=1162.56,  # 800 * 1.4532
            profit_loss=42.56,
            created_at=datetime(2023, 4, 15),
            updated_at=datetime.utcnow()
        )
    ]
    
    # 添加持仓数据
    for holding in holdings:
        db.add(holding)
    
    db.commit()
    
    return holdings

# 创建模拟交易记录
def create_mock_transactions(db, users, funds):
    """创建模拟交易记录"""
    transactions = []
    
    # 为每个用户创建一些交易记录
    for user in users:
        # 买入交易记录
        for i, fund in enumerate(funds[:2]):  # 每个用户买2只基金
            shares = 1000 + (i * 500)
            amount = shares * fund.latest_nav
            transaction_date = datetime.utcnow() - timedelta(days=30 - (i * 10))
            
            buy_transaction = Transaction(
                id=str(uuid.uuid4()),
                user_id=user.id,
                fund_id=fund.id,
                transaction_type="buy",
                amount=amount,
                shares=shares,
                unit_price=fund.latest_nav,
                transaction_price=fund.latest_nav,
                fee=amount * 0.015,  # 假设费率1.5%
                net_amount=amount + (amount * 0.015),
                status="completed",
                transaction_mode="one-time",
                transaction_date=transaction_date,
                created_at=transaction_date,
                updated_at=transaction_date,
                completed_at=transaction_date
            )
            transactions.append(buy_transaction)
        
        # 卖出部分份额的交易记录（只对第一只基金）
        if funds:
            sell_shares = 200
            sell_amount = sell_shares * funds[0].latest_nav
            sell_date = datetime.utcnow() - timedelta(days=5)
            
            sell_transaction = Transaction(
                id=str(uuid.uuid4()),
                user_id=user.id,
                fund_id=funds[0].id,
                transaction_type="sell",
                amount=sell_amount,
                shares=sell_shares,
                unit_price=funds[0].latest_nav,
                transaction_price=funds[0].latest_nav,
                fee=sell_amount * 0.005,  # 假设赎回费率0.5%
                net_amount=sell_amount - (sell_amount * 0.005),
                status="completed",
                transaction_mode="one-time",
                transaction_date=sell_date,
                created_at=sell_date,
                updated_at=sell_date,
                completed_at=sell_date
            )
            transactions.append(sell_transaction)
    
    # 添加交易记录
    for transaction in transactions:
        db.add(transaction)
    
    db.commit()
    
    return transactions

# 主函数
def main():
    """主函数，设置所有模拟数据"""
    print("开始设置模拟数据...")
    
    try:
        # 初始化数据库
        db = init_database()
        print("数据库初始化成功！")
        
        # 创建模拟基金数据
        print("创建模拟基金数据...")
        funds = create_mock_funds(db)
        print(f"成功创建 {len(funds)} 只基金及相关净值数据！")
        
        # 创建模拟用户数据
        print("创建模拟用户数据...")
        users = create_mock_users(db)
        print(f"成功创建 {len(users)} 个测试用户！")
        print("用户信息：")
        for user in users:
            print(f"  - 用户名: {user.username}, 密码: 12345678, 邮箱: {user.email}")
        
        # 创建模拟用户持仓数据
        print("创建模拟用户持仓数据...")
        holdings = create_mock_holdings(db, users, funds)
        print(f"成功创建 {len(holdings)} 条用户持仓记录！")
        
        # 创建模拟交易记录
        print("创建模拟交易记录...")
        transactions = create_mock_transactions(db, users, funds)
        print(f"成功创建 {len(transactions)} 条交易记录！")
        
        print("\n模拟数据设置完成！")
        print("您现在可以：")
        print("1. 运行用户服务：python user_service/main.py")
        print("2. 使用测试用户登录（用户名: testuser1/testuser2, 密码: 12345678）")
        print("3. 通过API对接前端进行开发测试")
        
    except Exception as e:
        print(f"设置模拟数据时发生错误：{e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭数据库连接
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    main()