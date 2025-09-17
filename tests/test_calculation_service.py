import unittest
import numpy as np
from datetime import datetime, timedelta
import json
from unittest.mock import patch, MagicMock
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculation_service.service import (
    calculate_impact_coefficient,
    calculate_fund_net_value
)

class TestCalculationService(unittest.TestCase):
    
    def setUp(self):
        # 准备测试数据
        self.current_time = datetime.utcnow()
        
        # 模拟新闻数据
        self.news_data = {
            'sentiment_score': 0.8,
            'published_at': self.current_time.isoformat() + 'Z',
            'source': 'xinhua',
            'keywords': ['environment', 'green', 'investment']
        }
        
        # 模拟基金ID
        self.fund_id = 'test-fund-id-001'
        
    @patch('calculation_service.service.redis_client')
    def test_calculate_impact_coefficient_recent_news(self, mock_redis):
        """测试计算最近新闻的影响系数"""
        # 配置Mock
        mock_redis.get.return_value = 'environment,green,ecology'.encode('utf-8')
        
        # 执行测试
        impact = calculate_impact_coefficient(self.news_data, self.fund_id)
        
        # 验证结果
        self.assertGreater(impact, 1.0, "正面新闻的影响系数应该大于1")
        self.assertLess(impact, 2.0, "影响系数不应超过2.0")
    
    @patch('calculation_service.service.redis_client')
    def test_calculate_impact_coefficient_old_news(self, mock_redis):
        """测试计算旧新闻的影响系数"""
        # 配置Mock
        mock_redis.get.return_value = 'environment,green,ecology'.encode('utf-8')
        
        # 创建一条5天前的新闻
        old_news = self.news_data.copy()
        old_time = self.current_time - timedelta(days=5)
        old_news['published_at'] = old_time.isoformat() + 'Z'
        
        # 执行测试
        impact_old = calculate_impact_coefficient(old_news, self.fund_id)
        impact_new = calculate_impact_coefficient(self.news_data, self.fund_id)
        
        # 验证结果
        self.assertLess(impact_old, impact_new, "旧新闻的影响系数应该小于新新闻")
    
    @patch('calculation_service.service.redis_client')
    def test_calculate_impact_coefficient_negative_news(self, mock_redis):
        """测试计算负面新闻的影响系数"""
        # 配置Mock
        mock_redis.get.return_value = 'environment,green,ecology'.encode('utf-8')
        
        # 创建一条负面新闻
        negative_news = self.news_data.copy()
        negative_news['sentiment_score'] = -0.8
        
        # 执行测试
        impact = calculate_impact_coefficient(negative_news, self.fund_id)
        
        # 验证结果
        self.assertLess(impact, 1.0, "负面新闻的影响系数应该小于1")
        self.assertGreater(impact, 0.1, "影响系数不应低于0.1")
    
    @patch('calculation_service.service.redis_client')
    @patch('calculation_service.service.requests.get')
    def test_calculate_fund_net_value_no_news(self, mock_requests, mock_redis):
        """测试不包含新闻影响的基金净值计算"""
        # 配置Mock
        mock_redis.get.return_value = json.dumps({'net_value': 1.0}).encode('utf-8')
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.json.return_value = []
        
        # 执行测试
        result = calculate_fund_net_value(
            self.fund_id, 
            include_news_impact=False,
            db=None
        )
        
        # 验证结果
        self.assertAlmostEqual(result['net_value'], 1.001, places=3)
        self.assertEqual(result['news_impact_count'], 0)
    
    @patch('calculation_service.service.redis_client')
    @patch('calculation_service.service.requests.get')
    def test_calculate_fund_net_value_with_news(self, mock_requests, mock_redis):
        """测试包含新闻影响的基金净值计算"""
        # 配置Mock
        mock_redis.get.return_value = json.dumps({'net_value': 1.0}).encode('utf-8')
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.json.return_value = [self.news_data]
        
        # 执行测试
        result = calculate_fund_net_value(
            self.fund_id, 
            include_news_impact=True,
            db=None
        )
        
        # 验证结果
        self.assertGreater(result['net_value'], 1.001)
        self.assertEqual(result['news_impact_count'], 1)
    
    @patch('calculation_service.service.redis_client')
    @patch('calculation_service.service.requests.get')
    def test_calculate_fund_net_value_with_adjustment(self, mock_requests, mock_redis):
        """测试包含调整因子的基金净值计算"""
        # 配置Mock
        mock_redis.get.return_value = json.dumps({'net_value': 1.0}).encode('utf-8')
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.json.return_value = []
        
        # 执行测试
        result = calculate_fund_net_value(
            self.fund_id, 
            include_news_impact=False,
            params={'adjustment': 0.05},
            db=None
        )
        
        # 验证结果
        self.assertAlmostEqual(result['net_value'], 1.05105, places=4)
    
    @patch('calculation_service.service.redis_client')
    @patch('calculation_service.service.requests.get')
    def test_calculate_fund_net_value_limits(self, mock_requests, mock_redis):
        """测试基金净值波动限制"""
        # 配置Mock
        mock_redis.get.return_value = json.dumps({'net_value': 1.0}).encode('utf-8')
        mock_requests.get.return_value.status_code = 200
        mock_requests.get.return_value.json.return_value = []
        
        # 执行测试 - 尝试大幅增加
        result = calculate_fund_net_value(
            self.fund_id, 
            include_news_impact=False,
            params={'adjustment': 0.5},
            db=None
        )
        
        # 验证结果 - 应该被限制在10%以内
        self.assertAlmostEqual(result['net_value'], 1.1, places=2)

if __name__ == '__main__':
    unittest.main()