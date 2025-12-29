"""
数据库连接配置
使用SQLite数据库
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

import sys
import os

# SQLite数据库文件路径
if getattr(sys, 'frozen', False):
    # 如果是打包后的 executable，数据库存放在 exe 同级目录
    BASE_DIR = os.path.dirname(sys.executable)
    DB_PATH = os.path.join(BASE_DIR, "bank_statement.db")
    DATABASE_URL = f"sqlite:///{DB_PATH}"
else:
    DATABASE_URL = "sqlite:///./bank_statement.db"

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite需要这个参数
)

# 创建Session工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    print("Starting database initialization...")
    Base.metadata.create_all(bind=engine)
    print("Database initialization completed")


def get_db():
    """
    获取数据库session（用于FastAPI依赖注入）

    使用方式：
    @app.get("/api/tasks")
    def get_tasks(db: Session = Depends(get_db)):
        tasks = db.query(Task).all()
        return tasks
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
