@echo off

@echo off

REM 设置UTF-8编码
chcp 65001 > nul

REM 检查是否安装了git
where git > nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Git not found. Please install Git first.
    pause
    exit /b 1
)

REM 获取当前分支名称
git branch --show-current > current_branch.txt 2>nul
set /p CURRENT_BRANCH=<current_branch.txt
del current_branch.txt

if "%CURRENT_BRANCH%"=="" (
    echo Error: Cannot determine current Git branch.
    pause
    exit /b 1
)

REM 简化界面
cls
echo =======================================================
echo Automatic GitHub Push Tool
Current Branch: %CURRENT_BRANCH%
echo =======================================================

REM 允许用户输入自定义提交消息
set /p "COMMIT_MSG=Enter commit message (Default: Update project files): "

REM 如果用户没有输入提交消息，使用默认消息
if "%COMMIT_MSG%"=="" set COMMIT_MSG=Update project files

REM 显示状态信息
echo Checking repository status...
git status -s

REM 添加所有已修改和未跟踪的文件
echo.
echo Adding files to staging area...
git add .

REM 检查添加是否成功
if %errorlevel% neq 0 (
    echo Error: Failed to add files!
    pause
    exit /b %errorlevel%
)

REM 提交更改
echo Committing changes...
git commit -m "%COMMIT_MSG%"

REM 检查是否有需要提交的更改
if %errorlevel% neq 0 (
    echo Warning: No changes to commit or commit failed.
    echo Trying to push directly...
    goto PUSH_STEP
)

:PUSH_STEP
REM 推送到远程仓库
echo Pushing to remote repository branch %CURRENT_BRANCH%...
git push origin %CURRENT_BRANCH%

REM 检查推送是否成功
if %errorlevel% neq 0 (
    echo Error: Push failed!
    echo 1. Check network connection
    echo 2. Check GitHub authentication
    echo 3. Check for branch conflicts
    echo 4. Check push permissions
    
    echo.
    echo Suggested solutions:
    echo - Configure Git user info:
    echo   git config --global user.name "Your GitHub Username"
    echo   git config --global user.email "Your GitHub Email"
    echo - For HTTPS, try entering GitHub credentials
    echo - For SSH, ensure SSH key is added to GitHub
    echo - If conflicted, pull latest code first
    
    pause
    exit /b %errorlevel%
)

REM 成功推送后的提示
echo.
echo =======================================================
echo Push successful!
echo All files have been pushed to GitHub branch %CURRENT_BRANCH%.
echo Vercel deployment will be triggered automatically.
echo You can check deployment status at: https://vercel.com/dashboard
echo =======================================================

REM 暂停以便用户查看结果
pause