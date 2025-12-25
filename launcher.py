"""
启动器 - 自动启动服务并打开浏览器
"""
import os
import sys
import time
import webbrowser
import threading
import subprocess
from pathlib import Path

def get_base_path():
    """获取应用基础路径（支持打包后的环境）"""
    if getattr(sys, 'frozen', False):
        # 打包后的exe运行环境
        return Path(sys._MEIPASS)
    else:
        # 开发环境
        return Path(__file__).parent

def start_backend_server():
    """启动后端服务器"""
    base_path = get_base_path()
    backend_dir = base_path / "backend"

    # 将backend目录添加到Python路径
    sys.path.insert(0, str(base_path))
    sys.path.insert(0, str(backend_dir))

    # 切换到backend目录
    os.chdir(str(backend_dir))

    # 导入并运行FastAPI应用
    import uvicorn

    # 动态导入main模块
    import importlib.util
    spec = importlib.util.spec_from_file_location("main", backend_dir / "main.py")
    main_module = importlib.util.module_from_spec(spec)
    sys.modules['main'] = main_module
    spec.loader.exec_module(main_module)
    app = main_module.app

    print("\n" + "="*60)
    print("  银行对账单生成系统 v1.0.0")
    print("="*60)
    print(f"\n  启动服务中...")
    print(f"  访问地址: http://localhost:8000")
    print("\n  按 Ctrl+C 或关闭窗口停止服务")
    print("="*60 + "\n")

    # 运行服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

def open_browser():
    """延迟打开浏览器"""
    time.sleep(3)  # 等待服务器启动
    url = "http://localhost:8000"
    print(f"\n正在打开浏览器访问: {url}\n")
    webbrowser.open(url)

def main():
    """主函数"""
    try:
        # 创建浏览器打开线程
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()

        # 启动后端服务器（阻塞运行）
        start_backend_server()

    except KeyboardInterrupt:
        print("\n\n服务已停止")
    except Exception as e:
        print(f"\n启动失败: {str(e)}")
        print("\n请检查:")
        print("1. Python环境是否正确安装")
        print("2. 依赖包是否完整")
        print("3. 端口8000是否被占用")
        input("\n按回车键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main()
