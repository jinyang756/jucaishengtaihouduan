import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime

# 导入我们需要测试的函数
from user_service.service import get_user_holdings, get_user_transactions

class TestUserService(unittest.TestCase):
    
    def setUp(self):
        # 创建模拟数据库会话
        self.mock_db = MagicMock()
        
        # 创建模拟用户
        self.mock_user = MagicMock()
        self.mock_user.id = "test_user_id"
        
        # 创建模拟基金
        self.mock_fund = MagicMock()
        self.mock_fund.id = "test_fund_id"
        self.mock_fund.code = "FUND001"
        self.mock_fund.name = "Test Fund"
        self.mock_fund.latest_nav = 1.2
        
        # 创建模拟持仓
        self.mock_holding = MagicMock()
        self.mock_holding.user_id = "test_user_id"
        self.mock_holding.fund_id = "test_fund_id"
        self.mock_holding.shares = 100
        self.mock_holding.purchase_price = 1.0
        
        # 创建模拟交易
        self.mock_transaction = MagicMock()
        self.mock_transaction.id = "test_transaction_id"
        self.mock_transaction.user_id = "test_user_id"
        self.mock_transaction.fund_id = "test_fund_id"
        self.mock_transaction.shares = 100
        self.mock_transaction.transaction_price = 1.1
        self.mock_transaction.transaction_type = "buy"
        self.mock_transaction.transaction_date = datetime.now()
        self.mock_transaction.status = "completed"
        
        # 配置mock行为
        self.mock_db.query.return_value.filter.return_value.first.return_value = self.mock_user
        
    def test_get_user_holdings(self):
        """测试获取用户持仓函数"""
        # 配置mock返回值
        self.mock_db.query.return_value.filter.return_value.all.return_value = [self.mock_holding]
        
        # 调用函数
        holdings = get_user_holdings("test_user_id", self.mock_db)
        
        # 验证结果
        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings[0]["fund_id"], "test_fund_id")
        self.assertEqual(holdings[0]["shares"], 100)
    
    def test_get_user_transactions(self):
        """测试获取用户交易记录函数"""
        # 配置mock返回值
        self.mock_db.query.return_value.filter.return_value.count.return_value = 1
        query_mock = MagicMock()
        query_mock.order_by.return_value.offset.return_value.limit.return_value.all.return_value = [self.mock_transaction]
        self.mock_db.query.return_value.filter.return_value = query_mock
        
        # 调用函数
        transactions_result = get_user_transactions("test_user_id", self.mock_db, page=1, per_page=10)
        
        # 验证结果
        self.assertEqual(len(transactions_result["transactions"]), 1)
        self.assertEqual(transactions_result["page"], 1)
        self.assertEqual(transactions_result["total"], 1)
        self.assertEqual(transactions_result["total_pages"], 1)

if __name__ == "__main__":
    unittest.main()