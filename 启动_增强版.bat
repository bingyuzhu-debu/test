@echo off
REM ============================================
REM 银行对账单生成系统 - 启动脚本（增强版）
REM 版本: 1.1.0
REM ============================================

REM 设置UTF-8编码
chcp 65001 >nul 2>&1

REM 设置窗口标题
title 银行对账单生成系统

REM 设置颜色（绿色）
color 0A

cls
echo.
echo ════════════════════════════════════════
echo   银行对账单生成系统 v1.0.0
echo ════════════════════════════════════════
echo.

REM ============================================
REM 步骤 1: 检查 Python 环境
REM ============================================
echo [步骤 1/4] 检查 Python 环境...

REM 尝试运行 python 命令
python --version >nul 2>&1
if %errorlevel% neq 0 (
    cls
    echo.
    echo ════════════════════════════════════════
    echo   ❌ 错误：未检测到 Python
    echo ════════════════════════════════════════
    echo.
    echo Python 未安装或未添加到系统 PATH。
    echo.
    echo 📥 请按照以下步骤安装 Python:
    echo.
    echo 1. 访问: https://www.python.org/downloads/
    echo 2. 下载 Python 3.9 或更高版本
    echo 3. 运行安装程序
    echo 4. ⚠️  务必勾选 "Add Python to PATH"
    echo 5. 点击 "Install Now"
    echo 6. 安装完成后重启电脑
    echo 7. 重新运行本程序
    echo.
    echo ════════════════════════════════════════
    echo.
    pause
    exit /b 1
)

REM 获取 Python 版本
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo    ✓ Python %PYTHON_VERSION% 已安装
echo.

REM ============================================
REM 步骤 2: 切换到正确的目录
REM ============================================
echo [步骤 2/4] 检查程序目录...

REM 切换到批处理文件所在目录
cd /d "%~dp0"

REM 检查 backend 目录
if not exist "backend" (
    cls
    echo.
    echo ════════════════════════════════════════
    echo   ❌ 错误：程序文件不完整
    echo ════════════════════════════════════════
    echo.
    echo 找不到 backend 目录！
    echo.
    echo 当前位置: %~dp0
    echo.
    echo 可能原因:
    echo - 压缩包解压不完整
    echo - 文件夹结构被破坏
    echo.
    echo 解决方法:
    echo - 重新解压完整的压缩包
    echo - 确保所有文件都解压到同一目录
    echo.
    echo ════════════════════════════════════════
    echo.
    pause
    exit /b 1
)

REM 切换到 backend 目录
cd backend

REM 检查主程序文件
if not exist "main.py" (
    echo    ❌ 错误: 找不到 main.py
    echo.
    pause
    exit /b 1
)

echo    ✓ 程序文件完整
echo.

REM ============================================
REM 步骤 3: 检查并安装依赖
REM ============================================
echo [步骤 3/4] 检查 Python 依赖库...

REM 检查 fastapi 是否已安装
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo    ⚠️  检测到首次运行，需要安装依赖库
    echo.
    echo    这可能需要 1-3 分钟，请耐心等待...
    echo.
    echo ────────────────────────────────────────

    REM 升级 pip
    echo    正在升级 pip...
    python -m pip install --upgrade pip --quiet

    REM 安装依赖
    echo    正在安装依赖库...
    python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple --quiet

    if %errorlevel% neq 0 (
        echo.
        echo    ❌ 依赖库安装失败！
        echo.
        echo    请检查:
        echo    1. 网络连接是否正常
        echo    2. 是否被防火墙拦截
        echo.
        echo    手动安装命令:
        echo    python -m pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )

    echo ────────────────────────────────────────
    echo    ✓ 依赖库安装成功！
    echo.
) else (
    echo    ✓ 依赖库已就绪
    echo.
)

REM ============================================
REM 步骤 4: 启动服务
REM ============================================
echo [步骤 4/4] 启动服务器...
echo.
echo ════════════════════════════════════════
echo   🚀 系统启动中...
echo ════════════════════════════════════════
echo.
echo   📌 访问地址: http://localhost:8000
echo.
echo   💡 使用说明:
echo      - 在浏览器中打开上述地址
echo      - 关闭本窗口将停止服务
echo      - 按 Ctrl+C 可以停止服务
echo.
echo ════════════════════════════════════════
echo.

REM 启动服务（如果失败，显示详细错误信息）
python main.py

REM 如果程序异常退出
if %errorlevel% neq 0 (
    echo.
    echo ════════════════════════════════════════
    echo   ❌ 程序启动失败
    echo ════════════════════════════════════════
    echo.
    echo 错误代码: %errorlevel%
    echo.
    echo 请将上述错误信息截图发送给技术支持。
    echo.
)

echo.
echo ════════════════════════════════════════
echo   程序已停止
echo ════════════════════════════════════════
echo.
pause
