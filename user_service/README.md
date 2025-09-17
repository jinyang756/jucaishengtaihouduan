# 用户服务 (User Service)

绿色生态基金虚拟净值模拟系统的用户服务模块，提供用户管理、资产管理和交易功能。

## 功能特性

- 用户注册与登录
- 用户信息管理
- 资产管理（余额、持仓）
- 基金交易（买入/卖出）
- 交易记录查询

## 目录结构

```
user_service/
├── __init__.py       # 模块初始化文件
├── models.py         # 数据模型定义
├── schemas.py        # 请求/响应模型定义
├── service.py        # 核心业务逻辑和API实现
├── main.py           # 服务入口文件
└── README.md         # 服务说明文档
```

## 主要API端点

### 用户管理
- `POST /users/register` - 用户注册
- `POST /users/login` - 用户登录
- `GET /users/{user_id}` - 获取用户信息
- `PUT /users/{user_id}` - 更新用户信息

### 资产管理
- `POST /users/{user_id}/balance/deposit` - 充值余额
- `POST /users/{user_id}/holdings` - 获取用户持仓列表
- `POST /users/{user_id}/transactions` - 获取用户交易记录

### 交易管理
- `POST /transactions` - 创建交易

## 部署配置

服务默认监听端口：8004

环境变量配置：
- `PORT` - 服务端口（默认：8004）
- `HOST` - 服务主机（默认：0.0.0.0）
- `RELOAD` - 是否启用自动重载（默认：true）
- 数据库配置通过 Edge Config 或环境变量 `DATABASE_URL` 提供

## 运行方式

```bash
# 直接运行
python main.py

# 或通过 uvicorn 运行
uvicorn service:app --host 0.0.0.0 --port 8004 --reload
```