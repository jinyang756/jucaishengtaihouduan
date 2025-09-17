# 聚财生态基金后端环境准备与服务启动指南

## 一、前提条件

在开始之前，请确保您的系统已安装以下软件：

- [Docker](https://www.docker.com/get-started)（推荐最新版本）
- [Docker Compose](https://docs.docker.com/compose/install/)（通常与Docker一起安装）
- [Python 3.8+](https://www.python.org/downloads/)（仅用于运行验证脚本）
- [Git](https://git-scm.com/downloads)（可选，用于代码管理）

## 二、环境准备

### 1. 获取项目代码

将项目代码复制到本地目录：

```bash
# 如果有Git仓库，使用git clone
# git clone <仓库地址> 

# 或者直接在本地准备项目代码
```

### 2. 配置环境变量

复制并编辑环境变量配置文件：

```bash
# Windows系统
copy .env.example .env

# Linux/Mac系统
export .env.example .env
```

打开`.env`文件，根据您的环境修改以下关键配置（开发环境可使用默认值）：

```
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=password
DB_NAME=green_ecology_fund

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379

# API服务配置
API_HOST=0.0.0.0
API_PORT=8080
DEBUG=True

# 安全配置
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here
```

## 三、启动服务

### 1. 构建和启动所有服务

使用Docker Compose构建并启动所有容器服务：

```bash
# Windows PowerShell
cd c:\Users\28163\Desktop\聚财生态基金后端

docker-compose up -d --build
```

此命令会：
- 构建项目的Docker镜像
- 下载所需的基础镜像（MariaDB、Redis等）
- 创建并启动所有服务容器
- 自动初始化MariaDB数据库（使用`database/init.sql`脚本）

### 2. 监控服务启动状态

可以使用以下命令查看容器启动状态：

```bash
docker-compose ps
```

等待几分钟，让所有服务完全启动。特别是数据库服务，需要时间进行初始化。

## 四、验证环境和服务健康状态

运行我们提供的环境验证脚本，检查所有组件是否正常工作：

```bash
# Windows PowerShell
python verify_environment.py
```

该脚本会自动检查：

1. **Docker容器状态**：确认所有必要的容器是否正在运行
2. **数据库初始化**：等待MariaDB初始化完成并检查连接
3. **数据库结构**：验证所有必要的表是否已创建
4. **示例数据**：检查是否已插入预期的示例数据
5. **API服务健康**：验证API网关和各个微服务是否正常响应

## 五、数据库初始化说明

项目使用`database/init.sql`脚本自动初始化MariaDB数据库，包括：

- 创建`green_ecology_fund`数据库（如果不存在）
- 创建所有必要的表结构：
  - `rules`（规则表）
  - `news`（新闻表）
  - `calculation_logs`（计算日志表）
  - `news_impacts`（新闻影响表）
  - `funds`（基金表）
  - `fund_net_values`（基金净值表）
- 插入示例数据，便于测试和开发

数据库初始化会在容器首次启动时自动执行。如果需要重新初始化数据库，可以执行以下命令：

```bash
# 停止并删除数据库容器和数据卷
docker-compose down -v

# 重新启动所有服务（会重新初始化数据库）
docker-compose up -d --build
```

## 六、访问服务

服务启动后，可以通过以下端口访问各个组件：

- **API网关**：http://localhost:8080
- **规则服务**：http://localhost:8000
- **新闻服务**：http://localhost:8001
- **计算服务**：http://localhost:8002
- **基金服务**：http://localhost:8003
- **MariaDB数据库**：localhost:3306（用户名：root，密码：password）
- **Redis**：localhost:6379
- **Prometheus监控**：http://localhost:9090
- **Grafana可视化**：http://localhost:3000（用户名：admin，密码：admin）

## 七、常见问题排查

### 1. 数据库连接失败

- 检查`.env`文件中的数据库配置是否正确
- 确认MariaDB容器已正常启动：`docker-compose logs mariadb`
- 检查容器网络是否正确配置：`docker-compose exec mariadb ping -c 3 api_gateway`

### 2. API服务无法访问

- 检查API服务容器日志：`docker-compose logs api_gateway`
- 确认容器端口映射是否正确：`docker-compose ps`
- 检查防火墙设置，确保相应端口已开放

### 3. 数据库初始化失败

- 查看数据库初始化日志：`docker-compose logs mariadb`
- 检查`database/init.sql`文件的语法是否正确
- 考虑手动初始化数据库：
  
  ```bash
  # 进入数据库容器
  docker-compose exec -it mariadb mysql -u root -ppassword
  
  # 在MySQL命令行中手动执行SQL脚本
  source /docker-entrypoint-initdb.d/init.sql;
  ```

## 八、下一步：功能测试

环境准备完成且所有服务健康运行后，可以开始进行功能测试：

1. **API端点测试**：使用Postman或curl测试各个API端点
2. **业务逻辑验证**：测试基金计算、新闻影响分析等核心功能
3. **数据一致性检查**：验证不同服务之间的数据是否一致
4. **性能测试**：在模拟负载下测试系统性能

具体的功能测试方法和测试用例请参考相关文档或创建专门的测试脚本。

## 九、停止服务

当您完成测试或开发后，可以使用以下命令停止所有服务：

```bash
# 停止并保留容器和数据
docker-compose down

# 停止并删除容器和数据卷（会丢失所有数据）
docker-compose down -v
```

---

通过本指南，您应该能够成功准备环境、启动服务并验证系统健康状态。如果遇到任何问题，请参考常见问题排查部分或联系技术支持。