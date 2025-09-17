# 聚财生态基金后端 - Vercel Serverless部署指南

## 项目概述

本指南将帮助您将聚财生态基金后端项目部署到Vercel平台上，使用Serverless Functions架构。

## 前提条件

- Vercel账户
- GitHub/GitLab/Bitbucket账户（用于代码托管）
- 数据库连接信息（MySQL/MariaDB）

## 部署准备

### 1. 项目结构调整

我们已经为您创建了以下关键文件，用于Vercel部署：

- `vercel.json` - Vercel部署配置
- `package.json` - Node.js配置
- `api/index.py` - Serverless函数入口点
- `api/requirements.txt` - Python依赖
- `api/.env.example` - 环境变量示例

### 2. 环境变量配置

在Vercel项目设置中，需要添加以下环境变量：

| 环境变量 | 说明 | 示例值 |
|---------|------|-------|
| `DATABASE_URL` | 数据库连接URL | `mariadb+mariadbconnector://username:password@host:port/database_name` |
| `FRONTEND_URL` | 前端应用URL | `https://your-frontend.vercel.app` |
| `SECRET_KEY` | 安全密钥（用于JWT等） | `your-secret-key` |
| `DB_HOST` | 数据库主机（可选，如不使用DATABASE_URL） | `db.example.com` |
| `DB_PORT` | 数据库端口（可选） | `3306` |
| `DB_USER` | 数据库用户名（可选） | `user` |
| `DB_PASSWORD` | 数据库密码（可选） | `password` |
| `DB_NAME` | 数据库名（可选） | `green_ecology_fund` |

## 部署步骤

### 1. 准备代码仓库

将项目代码推送到您的代码托管平台（GitHub、GitLab或Bitbucket）。

### 2. 在Vercel上导入项目

1. 登录Vercel控制台
2. 点击"New Project"按钮
3. 选择您的代码仓库
4. 点击"Import"按钮

### 3. 配置项目设置

1. 在"Configure Project"页面，保留默认的构建设置
2. **配置Edge Config（推荐）**：
     - 在Vercel控制台中，点击左侧菜单栏的 "Storage"
   - 点击 "Edge Config" 部分，找到已创建的名为 `jucaishengtai` 的配置
   - 在该Edge Config中，点击 "Add Item" 按钮添加以下数据库配置项：
     - `DB_HOST`: 您的数据库主机地址
     - `DB_PORT`: 数据库端口（通常为 3306）
     - `DB_USER`: 数据库用户名
     - `DB_PASSWORD`: 数据库密码
     - `DB_NAME`: 数据库名称（green_ecology_fund）
   - 点击 "Connect to Project"，选择您的项目，并在高级选项中确保环境变量名称为 `EDGE_CONFIG`
   
   **注意：** 您的Edge Config ID为：`ecfg_xfrfdjmkzodtkhqy4c8jhs0loyed`
   令牌为：`d5ba143a-2429-433b-a2cb-7f75161bd918`
   Digest为：`5bf6b008a9ec05f6870c476d10b53211797aa000f95aae344ae60f9b422286da`
3. **或配置环境变量**：
   - 展开"Environment Variables"部分
   - 添加上述所有必要的环境变量
4. 点击"Deploy"按钮开始部署
   - Vercel会自动执行以下命令：
     - 安装命令：`npm run install`（会执行 `pip install -r api/requirements.txt` 安装Python依赖）
     - 构建命令：`npm run build`（FastAPI应用不需要特殊构建步骤）

### 4. 完成部署

等待Vercel完成构建和部署过程。部署完成后，您将获得一个URL，类似于 `https://your-project.vercel.app`。

## 测试部署

部署完成后，您可以通过以下端点测试API：

- 健康检查：`https://your-project.vercel.app/api/health`
- 基金数据测试：`https://your-project.vercel.app/api/funds`
- API文档：`https://your-project.vercel.app/docs`
- WebSocket测试：可以使用WebSocket客户端连接到`wss://your-project.vercel.app/api/ws/your-client-id`
- Edge Config测试：`https://your-project.vercel.app/welcome`（测试Edge Config集成，返回问候语配置）

根据部署截图，您的项目已经成功部署到Vercel平台，访问地址为：`https://jucaishengtaihouduan.vercel.app`

## 开发环境运行

在本地开发环境中，您可以使用以下命令运行API：

```bash
cd api
pip install -r requirements.txt
python index.py
```

然后访问 `http://localhost:8080/api/health` 进行测试。

## 注意事项

1. Serverless环境中，连接可能会有冷启动延迟
2. 数据库连接字符串应当妥善保管，避免泄露
3. 对于生产环境，建议使用Vercel的环境变量加密功能
4. 如有长时间运行的任务，考虑使用Vercel Cron Jobs或其他异步处理方式
5. 定期检查Vercel控制台的函数执行日志，排查潜在问题

## 故障排查

### 常见问题

1. **数据库连接错误**
   - 检查DATABASE_URL是否正确
   - 确认数据库服务器允许外部连接
   - 验证数据库用户权限

2. **500内部服务器错误**
   - 查看Vercel日志了解详细错误信息
   - 检查依赖包是否正确安装
   - 验证代码中的错误处理逻辑

3. **CORS跨域问题**
   - 确保FRONTEND_URL环境变量已正确设置
   - 检查CORS中间件配置

## 相关资源

- [Vercel Python Runtime文档](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [Mangum文档](https://mangum.io/)

如果您在部署过程中遇到任何问题，请参考Vercel的官方文档或联系Vercel支持。

## WebSocket配置

本项目已配置WebSocket支持，您可以使用WebSocket进行实时通信。

### 配置说明

1. **vercel.json中的WebSocket配置**
   
   项目的vercel.json文件中已包含WebSocket的特殊路由配置：
   ```json
   {
     "version": 2,
     "builds": [
       {"src": "api/index.py", "use": "@vercel/python"}
     ],
     "routes": [
       {
         "src": "/api/ws",
         "dest": "api/index.py",
         "methods": ["GET"],
         "headers": {
           "Upgrade": "websocket",
           "Connection": "Upgrade"
         }
       },
       {
         "src": "/api/(.*)",
         "dest": "api/index.py"
       }
     ]
   }
   ```

2. **FastAPI WebSocket实现**
   
   api/index.py文件中实现了WebSocket功能，包括：
   - ConnectionManager类：管理WebSocket连接
   - WebSocket端点：处理客户端连接、消息接收和广播

### 使用方法

#### 后端WebSocket端点

- WebSocket端点：`/api/ws/{client_id}`
- 功能：支持客户端连接、消息发送和广播

#### 前端API客户端

项目提供了前端API客户端封装（api/client.js），包含：

- 常规HTTP请求方法（GET、POST、PUT、DELETE、PATCH）
- WebSocket连接管理方法

```javascript
// 使用示例
import { api } from './api/client';

// 发送HTTP请求
try {
  const funds = await api.get('/funds');
  console.log(funds);
} catch (error) {
  console.error('Failed to fetch funds:', error);
}

// 建立WebSocket连接
const ws = api.connectWebSocket(
  'unique-client-id',
  (message) => {
    console.log('Received message:', message);
  },
  (error) => {
    console.error('WebSocket error:', error);
  },
  (event) => {
    console.log('WebSocket closed:', event);
  }
);

// 发送WebSocket消息
if (ws && ws.readyState === WebSocket.OPEN) {
  ws.send('Hello from client!');
}
```

## 环境变量补充

除了之前提到的环境变量外，前端项目还需要配置以下环境变量：

```
NEXT_PUBLIC_API_URL=https://your-backend.vercel.app/api
NEXT_PUBLIC_WS_URL=wss://your-backend.vercel.app/api/ws
```

这些环境变量应在前端项目的Vercel设置中配置。