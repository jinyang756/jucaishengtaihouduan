# Windows系统Python安装指南

根据检查结果，您的系统中尚未安装Python或Python未正确配置在环境变量中。以下是在Windows系统上安装Python和pip的详细步骤。

## 1. 下载Python安装程序

1. 访问Python官方网站：[https://www.python.org/downloads/windows/](https://www.python.org/downloads/windows/)
2. 下载最新的Python 3.x版本（建议Python 3.8或更高版本）
3. 选择与您系统匹配的安装程序（通常是64位版本）

## 2. 安装Python

1. 运行下载的安装程序
2. **非常重要**：勾选底部的 "Add Python 3.x to PATH" 选项
3. 点击 "Install Now" 进行默认安装，或选择 "Customize installation" 进行自定义安装
4. 等待安装完成

## 3. 验证Python安装

1. 打开命令提示符（CMD）或PowerShell
2. 输入以下命令验证Python是否安装成功：
   ```
   python --version
   ```
3. 如果安装成功，将显示Python的版本号

## 4. 验证pip安装

Python安装通常会自动包含pip。要验证pip是否安装成功：

1. 在命令提示符（CMD）或PowerShell中输入：
   ```
   pip --version
   ```
2. 如果安装成功，将显示pip的版本号和所在路径

## 5. 常见问题解决

### 如果 `python --version` 命令无法识别

1. 检查是否在安装时勾选了 "Add Python 3.x to PATH" 选项
2. 如果没有勾选，您需要手动将Python添加到系统PATH环境变量：
   - 右键点击 "此电脑" -> "属性" -> "高级系统设置" -> "环境变量"
   - 在 "系统变量" 中找到 "Path"，点击 "编辑"
   - 添加Python的安装路径（通常是 `C:\Program Files\Python3x` 和 `C:\Program Files\Python3x\Scripts`）
   - 点击 "确定" 保存更改
   - 关闭并重新打开命令提示符或PowerShell

### 更新pip到最新版本

```
python -m pip install --upgrade pip
```

## 6. 安装项目依赖

安装好Python和pip后，您可以使用以下命令安装项目所需的依赖：

```
cd c:\Users\28163\Desktop\聚财生态基金后端
python -m pip install -r api/requirements.txt
```

## 7. 本地开发运行

安装完依赖后，您可以使用以下命令在本地运行项目：

```
# 方法1：使用uvicorn直接运行
cd c:\Users\28163\Desktop\聚财生态基金后端
uvicorn app:app --reload

# 方法2：使用Vercel CLI运行
cd c:\Users\28163\Desktop\聚财生态基金后端
vercel dev
```

安装完成后，您就可以在本地进行项目开发和测试了！