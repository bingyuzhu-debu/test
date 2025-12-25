@echo off
chcp 65001 >nul
echo ========================================
echo   银行对账单生成系统
echo   版本: 1.0.0
echo ========================================
echo.

echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未检测到 Python，请先安装 Python 3.9 或更高版本
    echo.
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo ✓ Python 已安装

echo.
echo [2/3] 检查依赖库...
cd /d "%~dp0backend"
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo 首次运行，正在安装依赖库...
    pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
    if %errorlevel% neq 0 (
        echo ❌ 依赖库安装失败，请检查网络连接
        pause
        exit /b 1
    )
)
echo ✓ 依赖库已就绪

echo.
echo [3/3] 启动服务...
echo.
echo ========================================
echo   系统已启动！
echo   请在浏览器中打开: http://localhost:8000
echo ========================================
echo.
echo 提示: 关闭此窗口将停止服务
echo.

python main.py

pause
