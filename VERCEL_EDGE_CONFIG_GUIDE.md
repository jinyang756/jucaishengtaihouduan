# Vercel Edge Config配置指南

本指南详细介绍如何在Vercel平台上配置和使用Edge Config来安全地存储和访问数据库连接信息。

## 为什么使用Edge Config？

Edge Config是Vercel提供的边缘配置存储服务，相比传统环境变量，它具有以下优势：

1. **安全性更高**：敏感数据（如数据库密码）不直接暴露在环境变量中
2. **实时更新**：配置变更无需重新部署应用即可生效
3. **版本控制**：配置变更有历史记录，支持回滚
4. **集中管理**：多个环境（开发、预览、生产）可共享或独立配置

## 步骤1：创建Edge Config

1. 登录Vercel控制台，选择您的项目
2. 点击左侧菜单栏的 **Storage**
3. 在 **Edge Config** 部分，点击 **Create Edge Config** 按钮
4. 输入名称（使用您提供的名称：`jucaishengtai`）
5. 点击 **Create** 按钮创建Edge Config

**注意：** 您的Edge Config ID为：`ecfg_xfrfdjmkzodtkhqy4c8jhs0loyed`
令牌为：`d5ba143a-2429-433b-a2cb-7f75161bd918`
Digest为：`5bf6b008a9ec05f6870c476d10b53211797aa000f95aae344ae60f9b422286da`

## 步骤2：添加数据库配置项

创建Edge Config后，您需要添加以下数据库配置项：

1. 在创建的Edge Config中，点击 **Add Item** 按钮
2. 依次添加以下键值对：
   
   | 键名 | 值类型 | 示例值 | 说明 |
   |------|--------|--------|------|
   | `DB_HOST` | 字符串 | `mysql.example.com` | 数据库主机地址 |
   | `DB_PORT` | 数字 | `3306` | 数据库端口（MySQL默认3306） |
   | `DB_USER` | 字符串 | `db_user` | 数据库用户名 |
   | `DB_PASSWORD` | 字符串 | `your-secure-password` | 数据库密码 |
   | `DB_NAME` | 字符串 | `green_ecology_fund` | 数据库名称 |
   
3. 添加完所有配置项后，点击页面顶部的 **Save** 按钮

## 步骤3：连接Edge Config到项目

1. 在Edge Config页面，点击右上角的 **Connect to Project** 按钮
2. 在弹出的对话框中，选择您要连接的项目
3. 展开 **Advanced Options** 部分
4. 确保 **Environment Variable** 字段的值为 `EDGE_CONFIG`（这是项目代码中配置的环境变量名称）
5. 在 **Environments** 部分，勾选需要启用此配置的环境（开发、预览、生产）
6. 点击 **Connect** 按钮完成连接

## 步骤4：验证配置是否生效

项目中已经实现了一个测试端点来验证Edge Config是否正常工作：

```python
# 已在api/index.py中实现的测试端点
@app.get("/welcome")
async def get_welcome_message():
    try:
        # 初始化EdgeConfig客户端
        edge_config = EdgeConfig()
        
        # 从Edge Config获取问候语配置
        greeting = await edge_config.get("greeting")
        
        # 如果配置存在，返回配置的问候语；否则返回默认问候语
        if greeting:
            return JSONResponse(content=greeting)
        else:
            return JSONResponse(content={"message": "Welcome to the Green Ecology Fund API!"})
    except Exception as e:
        logger.error(f"Error retrieving greeting from Edge Config: {e}")
        return JSONResponse(
            content={"error": "Failed to retrieve greeting", "details": str(e)},
            status_code=500
        )
```

部署后，访问 `/welcome` 端点来检查配置是否生效。如果Edge Config中配置了`greeting`值，将返回该配置；否则返回默认问候语。

根据部署截图，您的项目已经成功部署到Vercel平台，访问地址为：`https://jucaishengtaihouduan.vercel.app`

## 步骤5：更新现有配置

如果您需要更新数据库配置：

1. 登录Vercel控制台，进入您的项目
2. 点击左侧菜单栏的 **Storage** > **Edge Config**
3. 选择您之前创建的Edge Config
4. 点击要修改的配置项旁边的编辑图标
5. 更新值后点击 **Save** 按钮

注意：配置更新后会立即生效，无需重新部署应用。

## 配置优先级

项目的数据库连接逻辑会按照以下优先级获取配置：

1. 首先尝试从环境变量 `DATABASE_URL` 获取完整连接URL
2. 如果没有 `DATABASE_URL`，则尝试从Edge Config获取各个数据库连接参数
3. 如果Edge Config不可用，则使用代码中的默认配置

## 常见问题与解决方案

### 1. 连接数据库失败

**可能原因**：
- Edge Config中配置的值不正确
- Edge Config未正确连接到项目
- 数据库服务器不允许外部连接

**解决方案**：
- 检查Edge Config中的数据库配置值是否正确
- 确认项目中是否正确设置了 `EDGE_CONFIG` 环境变量
- 验证数据库服务器的网络访问权限

### 2. 无法访问Edge Config

**可能原因**：
- `vercel-edge-config` 包未安装
- `EDGE_CONFIG` 环境变量未正确设置
- Edge Config的访问权限问题

**解决方案**：
- 确保 `vercel-edge-config` 包已添加到 `api/requirements.txt` 中
- 确认Vercel项目中已正确配置 `EDGE_CONFIG` 环境变量
- 检查Edge Config的连接状态和权限设置

### 3. 配置变更后未生效

**可能原因**：
- 配置未保存
- 应用缓存了旧配置

**解决方案**：
- 确保在Edge Config页面点击了 **Save** 按钮
- 尝试重新部署应用以清除任何可能的缓存

## 安全注意事项

1. 不要在任何日志或API响应中暴露Edge Config中的敏感信息
2. 定期更新数据库密码并在Edge Config中同步更新
3. 限制对Edge Config的访问权限，仅授权必要人员
4. 启用Vercel的安全功能，如双重验证

## 备份与恢复

Vercel的Edge Config提供配置历史记录功能，您可以：

1. 查看配置的变更历史
2. 回滚到之前的配置版本
3. 导出配置作为备份

要访问这些功能，请在Edge Config页面点击右上角的 **Settings** 按钮。

---

通过正确配置Edge Config，您可以更安全、更灵活地管理数据库连接信息，同时享受实时更新和集中管理的便利。如果您在配置过程中遇到任何问题，请参考Vercel官方文档或联系Vercel支持。