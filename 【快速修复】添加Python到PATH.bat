@echo off
REM ============================================
REM 快速修复：将 Python 添加到系统 PATH
REM ============================================

chcp 65001 >nul 2>&1
color 0E
title 快速修复 - 添加Python到PATH

cls
echo.
echo ╔════════════════════════════════════════════════╗
echo ║  快速修复：添加 Python 到系统 PATH             ║
echo ╚════════════════════════════════════════════════╝
echo.
echo 此工具将帮助你把 Python 添加到系统环境变量
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

REM 检查 Python 是否已经在 PATH 中
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo.
    echo ✓ Python 已经在 PATH 中！
    echo.
    python --version
    echo.
    echo 您的 Python 可以正常使用，不需要修复。
    echo.
    echo 如果启动脚本仍然无法运行，请运行"诊断问题.bat"
    echo.
    pause
    exit /b 0
)

echo.
echo ❌ Python 未在 PATH 中检测到
echo.
echo 正在尝试自动查找 Python 安装位置...
echo.

REM 尝试在常见位置查找 Python
set PYTHON_FOUND=0

REM 检查 Python Launcher
py --version >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ 找到 Python Launcher (py.exe)
    echo.
    echo 您可以使用以下临时解决方案：
    echo.
    echo 1. 方案A - 创建专用启动脚本（推荐）
    echo    我将为您创建一个使用 py.exe 的启动脚本
    echo.
    choice /C YN /M "创建专用启动脚本"
    if !errorlevel!==1 (
        cd /d "%~dp0"
        (
            echo @echo off
            echo chcp 65001 ^>nul
            echo echo ========================================
            echo echo   银行对账单生成系统
            echo echo ========================================
            echo echo.
            echo cd /d "%%~dp0backend"
            echo py main.py
            echo pause
        ) > "启动_使用py.bat"

        echo.
        echo ✓ 已创建"启动_使用py.bat"
        echo.
        echo 请双击"启动_使用py.bat"来启动程序！
        echo.
        pause
        exit /b 0
    )

    set PYTHON_FOUND=1
)

REM 检查常见 Python 安装目录
for %%D in (
    "%LOCALAPPDATA%\Programs\Python\Python3*"
    "C:\Python3*"
    "C:\Program Files\Python3*"
    "C:\Program Files (x86)\Python3*"
    "%USERPROFILE%\AppData\Local\Programs\Python\Python3*"
) do (
    if exist "%%~D\python.exe" (
        echo 找到 Python: %%~D
        set PYTHON_PATH=%%~D
        set PYTHON_FOUND=1
        goto :FOUND
    )
)

:FOUND
if %PYTHON_FOUND% equ 0 (
    echo.
    echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    echo ❌ 未能自动找到 Python 安装位置
    echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    echo.
    echo 请选择以下方案之一：
    echo.
    echo 方案 1: 重新安装 Python（推荐）
    echo    1. 完全卸载当前的 Python
    echo    2. 访问: https://www.python.org/downloads/
    echo    3. 下载最新版本
    echo    4. 安装时务必勾选 "Add Python to PATH"
    echo    5. 重启电脑
    echo.
    echo 方案 2: 手动添加到 PATH
    echo    1. 找到 Python 安装目录（如 C:\Python311）
    echo    2. Win+R 输入: sysdm.cpl
    echo    3. 高级 → 环境变量
    echo    4. 系统变量 → Path → 编辑 → 新建
    echo    5. 添加 Python 安装目录和 Scripts 目录
    echo    6. 重启电脑
    echo.
    echo 方案 3: 联系技术支持
    echo    提供以下信息:
    echo    - Windows 版本
    echo    - Python 安装位置（如知道）
    echo    - 本诊断工具的输出截图
    echo.
    pause
    exit /b 1
)

echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo 找到 Python，但未添加到 PATH
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.
echo Python 位置: %PYTHON_PATH%
echo.
echo 警告: 自动修改系统 PATH 需要管理员权限
echo      且可能影响其他程序，不推荐自动操作
echo.
echo 推荐手动操作步骤：
echo.
echo 1. 按 Win+R，输入: sysdm.cpl，回车
echo 2. 点击"高级"标签页
echo 3. 点击"环境变量"按钮
echo 4. 在"系统变量"区域找到"Path"，双击
echo 5. 点击"新建"，添加以下两个路径:
echo    - %PYTHON_PATH%
echo    - %PYTHON_PATH%\Scripts
echo 6. 点击"确定"保存
echo 7. 重启电脑
echo 8. 重新运行本程序
echo.
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

pause
