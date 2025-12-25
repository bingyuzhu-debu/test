"""
数据库连接配置
使用SQLite数据库
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

# SQLite数据库文件路径
DATABASE_URL = "sqlite:///./bank_statement.db"

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite需要这个参数
)

# 创建Session工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """初始化数据库（创建所有表）"""
    Base.metadata.create_all(bind=engine)
    print("✓ 数据库初始化完成")


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
