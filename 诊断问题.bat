@echo off
chcp 65001 >nul
title 对账单工具 - 问题诊断
color 0A

echo.
echo ╔════════════════════════════════════════╗
echo ║  对账单工具 - 问题诊断程序             ║
echo ╚════════════════════════════════════════╝
echo.
echo 正在检查系统环境...
echo.

REM ============================================
REM 1. 检查当前目录
REM ============================================
echo [1] 当前目录:
cd
echo.

REM ============================================
REM 2. 检查 Python 是否安装
REM ============================================
echo [2] 检查 Python...
python --version 2>nul
if %errorlevel% neq 0 (
    echo.
    echo ❌ 错误: Python 未安装或未添加到系统 PATH
    echo.
    echo 解决方法:
    echo 1. 下载 Python: https://www.python.org/downloads/
    echo 2. 安装时务必勾选 "Add Python to PATH"
    echo 3. 重启电脑后再试
    echo.
    goto :ERROR
) else (
    echo ✓ Python 已安装
)
echo.

REM ============================================
REM 3. 检查 pip 是否可用
REM ============================================
echo [3] 检查 pip...
python -m pip --version 2>nul
if %errorlevel% neq 0 (
    echo ❌ pip 不可用
    goto :ERROR
) else (
    echo ✓ pip 可用
)
echo.

REM ============================================
REM 4. 检查目录结构
REM ============================================
echo [4] 检查目录结构...
if not exist "%~dp0backend" (
    echo ❌ 错误: backend 目录不存在！
    echo 当前位置: %~dp0
    echo.
    echo 可能原因:
    echo - 压缩包解压不完整
    echo - 文件夹被移动或删除
    echo.
    goto :ERROR
) else (
    echo ✓ backend 目录存在
)

if not exist "%~dp0backend\main.py" (
    echo ❌ 错误: main.py 文件不存在！
    goto :ERROR
) else (
    echo ✓ main.py 文件存在
)

if not exist "%~dp0backend\requirements.txt" (
    echo ❌ 错误: requirements.txt 文件不存在！
    goto :ERROR
) else (
    echo ✓ requirements.txt 文件存在
)

if not exist "%~dp0frontend" (
    echo ❌ 警告: frontend 目录不存在（前端界面可能无法显示）
) else (
    echo ✓ frontend 目录存在
)
echo.

REM ============================================
REM 5. 检查 Python 依赖
REM ============================================
echo [5] 检查 Python 依赖库...
cd /d "%~dp0backend"

python -c "import fastapi" 2>nul
if %errorlevel% neq 0 (
    echo ⚠ fastapi 未安装
    set NEED_INSTALL=1
) else (
    echo ✓ fastapi 已安装
)

python -c "import uvicorn" 2>nul
if %errorlevel% neq 0 (
    echo ⚠ uvicorn 未安装
    set NEED_INSTALL=1
) else (
    echo ✓ uvicorn 已安装
)

python -c "import sqlalchemy" 2>nul
if %errorlevel% neq 0 (
    echo ⚠ sqlalchemy 未安装
    set NEED_INSTALL=1
) else (
    echo ✓ sqlalchemy 已安装
)

echo.

if defined NEED_INSTALL (
    echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    echo 检测到缺少依赖库，是否现在安装？
    echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    echo.
    choice /C YN /M "安装依赖库"
    if %errorlevel%==1 (
        echo.
        echo 正在安装依赖库（可能需要 1-2 分钟）...
        echo.
        python -m pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
        if %errorlevel% neq 0 (
            echo.
            echo ❌ 依赖库安装失败！
            echo.
            echo 可能原因:
            echo - 网络连接问题
            echo - pip 版本过旧
            echo.
            echo 请尝试:
            echo 1. 检查网络连接
            echo 2. 升级 pip: python -m pip install --upgrade pip
            echo 3. 手动安装: python -m pip install -r requirements.txt
            echo.
            goto :ERROR
        ) else (
            echo.
            echo ✓ 依赖库安装成功！
        )
    )
)
echo.

REM ============================================
REM 6. 检查端口占用
REM ============================================
echo [6] 检查端口 8000 是否被占用...
netstat -ano | findstr ":8000" >nul
if %errorlevel%==0 (
    echo ⚠ 警告: 端口 8000 已被占用！
    echo.
    echo 可能原因:
    echo - 程序已经在运行
    echo - 其他程序占用了该端口
    echo.
    echo 解决方法:
    echo - 关闭其他占用 8000 端口的程序
    echo - 或修改 backend\main.py 中的端口号
    echo.
) else (
    echo ✓ 端口 8000 可用
)
echo.

REM ============================================
REM 7. 测试启动
REM ============================================
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 诊断完成！
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo 是否现在尝试启动程序？
echo.
choice /C YN /M "启动程序"
if %errorlevel%==1 (
    echo.
    echo 正在启动...
    echo.
    python main.py
)

goto :END

:ERROR
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 诊断未通过，请根据上述错误提示修复问题
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

:END
echo.
pause
