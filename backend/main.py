"""
FastAPI 主应用
提供银行对账单生成的Web API
"""

import sys
import webbrowser
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import shutil
from datetime import datetime
import uuid

from database import get_db, init_db
from models import Task
from services import BankStatementService

# 创建FastAPI应用
app = FastAPI(
    title="银行对账单生成系统",
    description="支持雷石天地、镭海、成都雷石三家公司的银行对账单生成",
    version="1.0.0"
)

# CORS配置（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 确定应用的基础路径和资源路径
if getattr(sys, 'frozen', False):
    # 如果是打包后的 executable
    # sys.executable 指向 exe 文件，dirname 得到 exe 所在目录（用于存储数据）
    BASE_DIR = os.path.dirname(sys.executable)
    # sys._MEIPASS 指向解压后的临时目录（用于读取打包的资源）
    RESOURCE_DIR = sys._MEIPASS
    # 前端文件在打包资源的 frontend 目录下
    FRONTEND_DIR = os.path.join(RESOURCE_DIR, "frontend")
else:
    # 正常 Python 运行环境
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

# 文件存储目录（在 exe 旁边的目录，保证数据持久化）
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")

# 确保目录存在
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)


@app.on_event("startup")
def startup_event():
    """应用启动时初始化数据库"""
    init_db()
    print("FastAPI app started successfully")
    print(f"Frontend static files dir: {FRONTEND_DIR}")
    print(f"Access URL: http://localhost:8000")
    # 自动打开浏览器
    try:
        webbrowser.open("http://localhost:8000")
        print("Browser opened automatically")
    except Exception as e:
        print(f"Failed to open browser: {e}")


# 挂载静态文件（前端资源）
if os.path.exists(FRONTEND_DIR):
    # 挂载静态资源（CSS/JS等）
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    # 首页路由 - 返回前端 index.html
    @app.get("/")
    def read_root():
        """返回前端首页"""
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
        return {"status": "ok", "message": "前端文件未找到"}


else:
    @app.get("/")
    def root():
        """健康检查接口"""
        return {
            "status": "ok",
            "message": "银行对账单生成系统 API 正在运行（前端文件未部署）",
            "version": "1.0.0"
        }


@app.post("/api/generate")
async def generate_statement(
    company: str = Form(..., description="公司名称：雷石天地/镭海/成都雷石"),
    month: str = Form(..., description="月份：YYYY-MM"),
    export_excel: bool = Form(True, description="导出Excel"),
    export_csv: bool = Form(False, description="导出CSV"),
    export_pdf: bool = Form(False, description="导出PDF"),
    file: UploadFile = File(..., description="底表Excel文件"),
    db: Session = Depends(get_db)
):
    """
    生成对账单

    Args:
        company: 公司名称（雷石天地/镭海/成都雷石）
        month: 月份（YYYY-MM格式）
        export_excel: 是否导出Excel
        export_csv: 是否导出CSV
        export_pdf: 是否导出PDF
        file: 上传的底表文件
        db: 数据库session

    Returns:
        任务结果，包含统计信息和下载链接
    """
    try:
        # 验证公司名称
        valid_companies = ['雷石天地', '镭海', '成都雷石']
        if company not in valid_companies:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的公司: {company}。支持的公司: {', '.join(valid_companies)}"
            )

        # 验证月份格式
        try:
            datetime.strptime(month, '%Y-%m')
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="月份格式错误，应为 YYYY-MM（如 2025-11）"
            )

        # 验证文件类型
        if not file.filename.endswith(('.xls', '.xlsx')):
            raise HTTPException(
                status_code=400,
                detail="只支持 .xls 或 .xlsx 格式的Excel文件"
            )

        # 保存上传的文件
        upload_filename = f"{uuid.uuid4()}_{file.filename}"
        upload_path = os.path.join(UPLOAD_DIR, upload_filename)

        with open(upload_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 创建任务记录（处理中状态）
        task = Task(
            company=company,
            month=month,
            uploaded_filename=file.filename,
            status='processing'
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        try:
            # 调用业务逻辑生成对账单
            service = BankStatementService(company, month, upload_path)
            result = service.generate_statement(OUTPUT_DIR)

            if result['status'] == 'failed':
                # 更新任务状态为失败
                task.status = 'failed'
                task.error_message = result['message']
                db.commit()

                raise HTTPException(
                    status_code=500,
                    detail=result['message']
                )

            # 更新任务记录（成功状态）
            task.status = 'completed'
            task.records_count = result['records_count']
            task.coverage_days = result['coverage_days']
            task.coverage_rate = result['coverage_rate']
            task.total_debit = result['total_debit']
            task.total_credit = result['total_credit']
            task.balance = result['balance']
            task.bank_details = result['bank_details']
            task.excel_path = result['excel_path']

            # 生成CSV和PDF（如果需要）
            if export_csv:
                from utils import export_to_csv
                csv_path = result['excel_path'].replace('.xls', '.csv')
                export_to_csv(result['excel_path'], csv_path)
                task.csv_path = csv_path

            if export_pdf:
                from utils import export_to_pdf
                pdf_path = result['excel_path'].replace('.xls', '.pdf')
                export_to_pdf(result['excel_path'], pdf_path, company, month)
                task.pdf_path = pdf_path

            db.commit()
            db.refresh(task)

            # 返回任务结果
            return {
                "status": "success",
                "message": result['message'],
                "task": task.to_dict()
            }

        except HTTPException:
            raise
        except Exception as e:
            # 记录详细错误日志
            import logging
            logging.getLogger("main").error(f"Generate statement failed: {str(e)}", exc_info=True)
            
            # 更新任务状态为失败
            task.status = 'failed'
            task.error_message = str(e)
            db.commit()

            raise HTTPException(
                status_code=500,
                detail=f"处理失败: {str(e)}"
            )

        finally:
            # 清理上传的临时文件
            if os.path.exists(upload_path):
                os.remove(upload_path)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"系统错误: {str(e)}"
        )


@app.get("/api/history")
def get_history(
    company: Optional[str] = None,
    month: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    查询历史记录

    Args:
        company: 筛选公司（可选）
        month: 筛选月份（可选）
        status: 筛选状态（可选：processing/completed/failed）
        limit: 每页数量（默认50）
        offset: 偏移量（默认0）
        db: 数据库session

    Returns:
        历史记录列表
    """
    try:
        # 构建查询
        query = db.query(Task)

        if company:
            query = query.filter(Task.company == company)

        if month:
            query = query.filter(Task.month == month)

        if status:
            query = query.filter(Task.status == status)

        # 按创建时间倒序
        query = query.order_by(Task.created_at.desc())

        # 获取总数
        total = query.count()

        # 分页
        tasks = query.offset(offset).limit(limit).all()

        return {
            "status": "success",
            "total": total,
            "limit": limit,
            "offset": offset,
            "data": [task.to_dict() for task in tasks]
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"查询失败: {str(e)}"
        )


@app.get("/api/task/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    """
    获取单个任务详情

    Args:
        task_id: 任务ID
        db: 数据库session

    Returns:
        任务详情
    """
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"任务不存在: {task_id}"
        )

    return {
        "status": "success",
        "data": task.to_dict()
    }


@app.get("/api/download/{task_id}/{format}")
def download_file(
    task_id: int,
    format: str,
    db: Session = Depends(get_db)
):
    """
    下载生成的文件

    Args:
        task_id: 任务ID
        format: 文件格式（excel/csv/pdf）
        db: 数据库session

    Returns:
        文件下载响应
    """
    # 查询任务
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"任务不存在: {task_id}"
        )

    # 根据格式获取文件路径
    file_path = None
    media_type = None

    if format == 'excel':
        file_path = task.excel_path
        media_type = "application/vnd.ms-excel"
    elif format == 'csv':
        file_path = task.csv_path
        media_type = "text/csv"
    elif format == 'pdf':
        file_path = task.pdf_path
        media_type = "application/pdf"
    else:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的格式: {format}。支持的格式: excel, csv, pdf"
        )

    # 检查文件是否存在
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"文件不存在: {format}"
        )

    # 生成下载文件名
    filename = os.path.basename(file_path)

    # 返回文件
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )


@app.delete("/api/task/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """
    删除任务记录及相关文件

    Args:
        task_id: 任务ID
        db: 数据库session

    Returns:
        删除结果
    """
    # 查询任务
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=404,
            detail=f"任务不存在: {task_id}"
        )

    # 删除相关文件
    for file_path in [task.excel_path, task.csv_path, task.pdf_path]:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"删除文件失败: {file_path}, 错误: {str(e)}")

    # 删除数据库记录
    db.delete(task)
    db.commit()

    return {
        "status": "success",
        "message": f"任务 {task_id} 已删除"
    }


@app.get("/api/stats")
def get_statistics(db: Session = Depends(get_db)):
    """
    获取统计信息

    Returns:
        统计数据
    """
    try:
        total_tasks = db.query(Task).count()
        completed_tasks = db.query(Task).filter(Task.status == 'completed').count()
        failed_tasks = db.query(Task).filter(Task.status == 'failed').count()
        processing_tasks = db.query(Task).filter(Task.status == 'processing').count()

        # 按公司统计
        company_stats = {}
        for company in ['雷石天地', '镭海', '成都雷石']:
            count = db.query(Task).filter(
                Task.company == company,
                Task.status == 'completed'
            ).count()
            company_stats[company] = count

        return {
            "status": "success",
            "data": {
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "failed_tasks": failed_tasks,
                "processing_tasks": processing_tasks,
                "company_stats": company_stats
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"统计查询失败: {str(e)}"
        )


# 捕获所有其他路由，放置在最后防止覆盖API路由
@app.get("/{full_path:path}")
def catch_all(full_path: str):
    """捕获所有前端路由"""
    # 如果是 API 请求，不处理 (理论上这行不会被执行，除非API真的不存在)
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API 路由不存在")

    # 返回前端 index.html
    if os.path.exists(FRONTEND_DIR):
        index_path = os.path.join(FRONTEND_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)

    raise HTTPException(status_code=404, detail="页面不存在")


if __name__ == "__main__":
    import uvicorn

    print("\n" + "="*50)
    print("  银行对账单生成系统 v1.0.0")
    print("="*50)
    print(f"\n  访问地址: http://localhost:8000")
    print(f"  API文档: http://localhost:8000/docs")
    print("\n  按 Ctrl+C 停止服务\n")
    print("="*50 + "\n")

    # 生产环境运行（不启用热重载）
    # 修复无终端模式下 uvicorn 日志报错的问题
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")

    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_config=None, # Disable uvicorn's default logging config
        )
    except Exception as e:
        # 尝试弹窗报错 (仅 Windows)
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, f"程序启动失败: {str(e)}", "错误", 0x10)
        except:
            pass
