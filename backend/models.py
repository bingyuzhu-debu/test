"""
数据库模型定义
使用SQLAlchemy ORM
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Task(Base):
    """对账单生成任务表"""
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, index=True)

    # 基本信息
    company = Column(String, nullable=False, index=True)  # 公司名称
    month = Column(String, nullable=False, index=True)    # 月份 YYYY-MM

    # 时间信息
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # 处理状态
    status = Column(String, default='processing')  # processing/completed/failed
    error_message = Column(String, nullable=True)  # 错误信息

    # 统计数据
    records_count = Column(Integer, default=0)     # 总记录数
    coverage_days = Column(Integer, default=0)     # 覆盖天数
    coverage_rate = Column(Float, default=0.0)     # 覆盖率
    total_debit = Column(Float, default=0.0)       # 借方总额
    total_credit = Column(Float, default=0.0)      # 贷方总额
    balance = Column(Float, default=0.0)           # 差额

    # 银行明细（JSON格式存储）
    # [{"name": "中信", "records": 88, "debit": 1416399.37, "credit": 1465310.91}]
    bank_details = Column(JSON, nullable=True)

    # 文件路径
    excel_path = Column(String, nullable=True)
    csv_path = Column(String, nullable=True)
    pdf_path = Column(String, nullable=True)

    # 上传的底表文件名（记录用）
    uploaded_filename = Column(String, nullable=True)

    def to_dict(self):
        """转换为字典（用于API返回）"""
        return {
            'id': self.id,
            'company': self.company,
            'month': self.month,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status,
            'error_message': self.error_message,
            'records_count': self.records_count,
            'coverage': f"{self.coverage_days}/{self._get_total_days()}天 ({self.coverage_rate:.1f}%)",
            'total_debit': self.total_debit,
            'total_credit': self.total_credit,
            'balance': self.balance,
            'bank_details': self.bank_details,
            'downloads': {
                'excel': f'/api/download/{self.id}/excel' if self.excel_path else None,
                'csv': f'/api/download/{self.id}/csv' if self.csv_path else None,
                'pdf': f'/api/download/{self.id}/pdf' if self.pdf_path else None,
            }
        }

    def _get_total_days(self):
        """根据月份计算总天数"""
        import calendar
        if not self.month:
            return 0
        try:
            year, month = map(int, self.month.split('-'))
            return calendar.monthrange(year, month)[1]
        except:
            return 0
