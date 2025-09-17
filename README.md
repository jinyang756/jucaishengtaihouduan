# 聚财生态基金系统

## 项目介绍
聚财生态基金系统是一个基于微服务架构的智能基金管理系统，能够根据新闻事件和市场规则自动计算基金净值，提供实时的基金管理和投资决策支持。

系统支持虚拟净值模拟、新闻事件影响分析、规则化投资决策、用户交易管理等功能，并通过Vercel Edge Config进行安全高效的配置管理。系统还实现了灵活的交易限额机制，可配置单笔交易金额限制、每日累计交易金额限制和每日交易笔数限制。

## 系统架构
本系统采用微服务架构，由以下几个核心服务组成：
- **API服务**：作为系统的主要入口点，提供REST API接口
- **API网关服务**：负责请求路由、负载均衡和安全认证
- **规则服务**：管理基金计算规则的配置和更新
- **新闻服务**：采集、分析和处理与基金相关的新闻信息
- **计算服务**：根据规则和新闻计算基金净值
- **基金服务**：管理基金的基本信息和净值历史数据
- **用户服务**：管理用户账户、认证和授权
- **公共服务**：提供共享的缓存等功能
- **配置管理**：基于Vercel Edge Config的配置管理系统

## 目录结构
```
├── api/                # API服务（主要入口点）
│   ├── index.py        # API主程序
│   ├── vercel_edge_config.py # Vercel Edge Config客户端
│   └── requirements.txt # API服务依赖
├── api_gateway/        # API网关服务
│   ├── __init__.py
│   └── app.py          # API网关主程序
├── common/             # 公共服务
│   ├── __init__.py
│   └── cache.py        # Redis缓存实现
├── config/             # 配置文件
│   ├── config.py       # 全局配置
│   └── prometheus.yml  # Prometheus监控配置
├── calculation_service/ # 计算服务
│   ├── __init__.py
│   ├── models.py       # 数据模型
│   ├── schemas.py      # 请求/响应模型
│   └── service.py      # 服务实现
├── fund_service/       # 基金服务
│   ├── __init__.py
│   ├── models.py       # 数据模型
│   ├── schemas.py      # 请求/响应模型
│   └── service.py      # 服务实现
├── news_service/       # 新闻服务
│   ├── __init__.py
│   ├── models.py       # 数据模型
│   ├── schemas.py      # 请求/响应模型
│   └── service.py      # 服务实现
├── rule_service/       # 规则服务
│   ├── __init__.py
│   ├── models.py       # 数据模型
│   ├── schemas.py      # 请求/响应模型
│   └── service.py      # 服务实现
├── user_service/       # 用户服务
│   ├── __init__.py
│   ├── main.py         # 用户服务主程序
│   ├── models.py       # 数据模型
│   ├── schemas.py      # 请求/响应模型
│   └── service.py      # 服务实现
├── database/           # 数据库相关文件
│   ├── __init__.py
│   ├── database.py     # 数据库连接配置
│   └── init.sql        # 数据库初始化SQL
├── .env.example        # 环境变量示例
├── .gitignore          # Git忽略规则
├── DEPLOYMENT_GUIDE.md # 部署指南
├── Dockerfile          # Docker构建文件
├── docker-compose.yml  # Docker Compose配置
├── EDGE_CONFIG_README.md # Edge Config配置文档
├── README.md           # 项目说明文档
├── comprehensive_test.py # 全面测试脚本
├── requirements.txt    # Python项目依赖
└── vercel.json         # Vercel部署配置
```

## 技术栈
- **后端框架**：FastAPI (Python)
- **数据库**：MySQL 8.0
- **缓存**：Redis 6
- **容器化**：Docker, Docker Compose
- **监控**：Prometheus, Grafana
- **ORM**：SQLAlchemy
- **数据验证**：Pydantic
- **API文档**：Swagger UI (自动生成)
- **配置管理**：Vercel Edge Config
- **环境变量管理**：python-dotenv
- **部署平台**：Vercel (支持)

## 快速开始

### 使用Docker Compose启动（推荐）
1. 克隆项目代码
   ```bash
   git clone [repository-url]
   cd 聚财生态基金
   ```

2. 复制环境变量示例文件
   ```bash
   cp .env.example .env
   # 根据需要修改.env文件中的配置
   ```

3. 启动所有服务
   ```bash
   docker-compose up -d --build
   ```

4. 访问服务
   - API网关：http://localhost:8080
   - Swagger文档：http://localhost:8080/docs
   - Grafana监控：http://localhost:3000 (初始账号/密码: admin/admin)
   - Prometheus：http://localhost:9090

### 本地开发环境设置
1. 安装Python 3.9或更高版本

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 启动数据库和Redis
   ```bash
   docker-compose up -d mysql redis
   ```

4. 运行单个服务（以API网关为例）
   ```bash
   python -m api_gateway.app
   ```

## API文档
系统自动生成Swagger UI文档，访问各服务的/docs路径即可查看详细的API接口说明。

### 主要API端点

#### API网关
- GET /health - 健康检查
- GET /status - 服务状态

#### 规则服务
- POST /rules - 创建规则
- GET /rules/{rule_id} - 获取规则详情
- PUT /rules/{rule_id} - 更新规则
- PATCH /rules/{rule_id}/status - 更新规则状态
- GET /rules/fund-type/{fund_type} - 获取指定基金类型的规则

#### 新闻服务
- POST /news - 创建新闻
- GET /news/{news_id} - 获取新闻详情
- PUT /news/{news_id} - 更新新闻
- POST /news/crawl - 爬取新闻
- POST /news/process/{news_id} - 处理新闻

#### 计算服务
- POST /calculation/net-value - 计算基金净值
- GET /calculation/historical/{fund_id} - 获取历史净值
- POST /calculation/news-impact - 评估新闻影响
- POST /calculation/batch - 批量计算

#### 基金服务
- POST /funds - 创建基金
- GET /funds/{fund_id} - 获取基金详情
- PUT /funds/{fund_id} - 更新基金
- GET /funds - 查询基金列表
- POST /funds/{fund_id}/nav - 添加基金净值
- GET /funds/{fund_id}/performance - 获取基金绩效

#### 用户服务
- POST /register - 用户注册
- POST /login - 用户登录
- GET /users/me - 获取当前用户信息
- GET /users/balance - 查询用户余额
- POST /users/balance/deposit - 存款
- POST /users/balance/withdraw - 提现
- POST /transactions - 创建交易（买入/卖出基金）
- GET /users/holdings - 查询用户持仓
- GET /users/transactions - 查询用户交易记录

## 配置说明
所有配置通过环境变量或.env文件设置，主要配置项包括：
- 数据库连接信息
- Redis连接信息
- API服务端口和主机
- 微服务URL
- 爬虫配置
- 计算参数配置
- 交易限额配置（单笔交易金额、每日累计金额、每日交易笔数）

## 监控与日志
- 服务指标通过Prometheus收集，Grafana可视化展示
- 日志通过标准输出记录，可通过Docker日志查看

## 部署指南
1. 准备生产环境的.env文件
2. 执行docker-compose up -d --build
3. 配置反向代理（如Nginx）
4. 设置SSL证书

## 开发指南
1. 遵循FastAPI和Pydantic的最佳实践
2. 新功能应在对应服务模块中实现
3. 所有API端点应有适当的文档和验证
4. 代码提交前运行测试

## 鸣谢
感谢所有为该项目做出贡献的开发者和测试人员。

## 许可证
[MIT License](LICENSE)