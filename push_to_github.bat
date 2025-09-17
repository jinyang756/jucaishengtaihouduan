@echo off

REM 设置UTF-8编码
chcp 65001 > nul

REM 添加所有已修改和未跟踪的文件
echo 正在添加文件到暂存区...
git add .

REM 检查添加是否成功
if %errorlevel% neq 0 (
    echo 添加文件失败！请检查是否有文件权限问题。
    pause
    exit /b %errorlevel%
)

REM 提交更改
echo 正在提交更改...
git commit -m "更新项目文件"

REM 检查提交是否成功
if %errorlevel% neq 0 (
    echo 提交失败！请检查git配置是否正确。
    pause
    exit /b %errorlevel%
)

REM 推送到远程仓库
echo 正在推送到远程仓库...
git push origin master

REM 检查推送是否成功
if %errorlevel% neq 0 (
    echo 推送失败！请检查网络连接和GitHub认证是否正确。
    echo 您可能需要先运行: git config --global user.name "您的用户名"
    echo 然后运行: git config --global user.email "您的邮箱"
    echo 如果还是失败，可能需要重新配置SSH密钥或使用HTTPS凭据。
    pause
    exit /b %errorlevel%
)

echo 推送成功！所有文件已成功推送到GitHub仓库。
pause