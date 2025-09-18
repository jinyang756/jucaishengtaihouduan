# 聚财生态基金系统

## 项目介绍
聚财生态基金系统是一个基于微服务架构的智能基金管理系统，能够根据新闻事件和市场规则自动计算基金净值，提供实时的基金管理和投资决策支持。

系统支持虚拟净值模拟、新闻事件影响分析、规则化投资决策、用户交易管理等功能，并通过Vercel Edge Config进行安全高效的配置管理。系统还实现了灵活的交易限额机制，可配置单笔交易金额限制、每日累计交易金额限制和每日交易笔数限制。

## 系统架构
本系统采用微服务架构，由以下几个核心服务组成：
- **API服务**：作为系统的主要入口点，提供REST API接口
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
│   ├── .env.example    # 环境变量示例
│   ├── index.py        # API主程序
│   └── requirements.txt # API服务依赖
├── calculation_service/ # 计算服务
│   ├── __init__.py
│   ├── models.py       # 数据模型
│   ├── schemas.py      # 请求/响应模型
│   └── service.py      # 服务实现
├── common/             # 公共服务
│   ├── __init__.py
│   └── cache.py        # Redis缓存实现
├── config/             # 配置文件
│   ├── config.py       # 全局配置
│   └── prometheus.yml  # Prometheus监控配置
├── database/           # 数据库相关文件
│   ├── __init__.py
│   ├── database.py     # 数据库连接配置
│   └── init.sql        # 数据库初始化SQL
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
├── push_to_github.bat  # 自动推送脚本
├── requirements.txt    # Python项目依赖
├── rule_service/       # 规则服务
│   ├── __init__.py
│   ├── models.py       # 数据模型
│   ├── schemas.py      # 请求/响应模型
│   └── service.py      # 服务实现
├── user_service/       # 用户服务
│   ├── README.md
│   ├── __init__.py
│   ├── main.py         # 用户服务主程序
│   ├── models.py       # 数据模型
│   ├── schemas.py      # 请求/响应模型
│   ├── service.py      # 服务实现
│   └── service_analysis_report.md
├── .env.example        # 环境变量示例
├── .gitignore          # Git忽略规则
├── DEPLOYMENT_GUIDE.md # 部署指南
├── ENVIRONMENT_SETUP_GUIDE.md # 环境设置指南
├── README.md           # 项目说明文档
├── SECURITY_BEST_PRACTICES.md # 安全最佳实践
├── vercel.json         # Vercel部署配置
└── 聚财生态基金后端开发事项.md # 开发事项记录
```

## 技术栈
- **后端框架**：FastAPI (Python)
- **数据库**：MySQL 8.0
- **缓存**：Redis 6
- **ORM**：SQLAlchemy
- **数据验证**：Pydantic
- **API文档**：Swagger UI (自动生成)
- **配置管理**：Vercel Edge Config
- **环境变量管理**：python-dotenv
- **部署平台**：Vercel

## 快速开始

### Vercel部署（推荐）
项目已成功配置为可在Vercel平台上部署，详细部署步骤请参考 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) 文件。

### 本地开发环境设置
1. 安装Python 3.9或更高版本

2. 安装依赖
   ```bash
   pip install -r requirements.txt
   ```

3. 复制环境变量示例文件
   ```bash
   cp .env.example .env
   # 根据需要修改.env文件中的配置
   ```

4. 运行API服务
   ```bash
   python app.py
   ```

## API文档
系统自动生成Swagger UI文档，部署后可通过以下路径查看详细的API接口说明：
- Swagger文档：`http://[部署域名]/docs`

### 主要API端点

#### 核心服务
- GET / - 服务欢迎页面
- GET /health - 健康检查
- GET /welcome - 欢迎信息

## 配置说明
所有配置通过环境变量或.env文件设置，主要配置项包括：
- 数据库连接信息
- Redis连接信息
- API服务端口和主机
- 微服务URL
- 计算参数配置
- 交易限额配置（单笔交易金额、每日累计金额、每日交易笔数）

## 部署指南

### Vercel部署
项目已配置与GitHub的自动部署集成，详细步骤请参考 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)。

Vercel配置说明：
- Python版本：3.9
- 构建配置：处理API入口和依赖安装
- 函数配置：设置内存限制为1024MB，超时时间为30秒

## 开发指南
1. 遵循FastAPI和Pydantic的最佳实践
2. 新功能应在对应服务模块中实现
3. 所有API端点应有适当的文档和验证
4. 代码提交前运行测试

## 自动推送脚本使用指南
项目根目录下提供了`push_to_github.bat`脚本，用于一键完成代码提交和推送，步骤如下：

1. 双击运行 `push_to_github.bat` 文件
2. 脚本会自动检测当前Git分支
3. 根据提示输入提交消息（可选，默认为"更新项目文件"）
4. 脚本会自动执行以下操作：
   - 添加所有修改和未跟踪的文件到暂存区
   - 提交更改
   - 推送到GitHub仓库的对应分支
5. 成功后会显示Vercel部署提示

### 注意事项
- 请确保代码通过本地测试后再推送
- 使用有意义的提交消息，清晰描述更改内容
- 推送后可在Vercel控制台查看部署状态
- 如遇部署失败，查看Vercel日志排查问题

## 许可证
[MIT License](LICENSE)