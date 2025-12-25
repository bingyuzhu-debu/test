@echo off
chcp 65001 >nul
echo ========================================
echo   银行对账单生成系统 - Windows打包脚本
echo ========================================
echo.

echo [1/4] 检查Python环境...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.9+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version

echo.
echo [2/4] 安装项目依赖...
cd backend
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ 安装依赖失败
    pause
    exit /b 1
)
cd ..

echo.
echo [3/4] 安装PyInstaller...
pip install pyinstaller
if %errorlevel% neq 0 (
    echo ❌ 安装PyInstaller失败
    pause
    exit /b 1
)

echo.
echo [4/4] 开始打包exe...
pyinstaller build_exe.spec --clean --noconfirm
if %errorlevel% neq 0 (
    echo ❌ 打包失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ 打包完成！
echo ========================================
echo.
echo 生成的文件位置: dist\银行对账单生成系统.exe
echo.
echo 说明:
echo 1. 双击 exe 文件即可启动
echo 2. 会自动打开浏览器访问系统
echo 3. 首次运行可能需要几秒钟初始化
echo.
pause
