"""
业务逻辑服务
调用现有的Python脚本生成对账单
"""

import sys
import os
from pathlib import Path
import xlrd
import xlwt
from datetime import datetime
import calendar

# 添加现有脚本的路径
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import generate_statement_leishi_tiandi
import generate_statement_leihai
import generate_statement_chengdu_leishi

# 公司配置映射
COMPANY_CONFIG = {
    '雷石天地': {
        'script_class': generate_statement_leishi_tiandi.BankStatementGenerator,
        'script_file': 'generate_statement_leishi_tiandi.py',
        'bank_count': 12
    },
    '镭海': {
        'script_class': generate_statement_leihai.LeihaiStatementGenerator,
        'script_file': 'generate_statement_leihai.py',
        'bank_count': 2
    },
    '成都雷石': {
        'script_class': generate_statement_chengdu_leishi.ChengduLeishiStatementGenerator,
        'script_file': 'generate_statement_chengdu_leishi.py',
        'bank_count': 2
    }
}


class BankStatementService:
    """银行对账单生成服务"""

    def __init__(self, company: str, month: str, uploaded_file_path: str):
        """
        初始化服务

        Args:
            company: 公司名称（雷石天地/镭海/成都雷石）
            month: 月份（YYYY-MM）
            uploaded_file_path: 用户上传的底表文件路径
        """
        self.company = company
        self.month = month
        self.uploaded_file_path = uploaded_file_path
        self.config = COMPANY_CONFIG.get(company)

        if not self.config:
            raise ValueError(f"不支持的公司: {company}")

    def generate_statement(self, output_dir: str) -> dict:
        """
        生成对账单

        Args:
            output_dir: 输出目录

        Returns:
            dict: 生成结果
            {
                'status': 'success/failed',
                'message': '处理信息',
                'records_count': 91,
                'coverage_days': 30,
                'coverage_rate': 100.0,
                'total_debit': 1917122.66,
                'total_credit': 1466446.91,
                'balance': 450675.75,
                'bank_details': [...],
                'excel_path': '/path/to/excel'
            }
        """
        try:
            # 获取对应的生成器类
            generator_class = self.config['script_class']

            # 创建生成器实例
            generator = generator_class(self.uploaded_file_path)

            # 加载工作簿
            if not generator.load_workbook():
                return {
                    'status': 'failed',
                    'message': '文件加载失败'
                }

            # 处理所有sheet
            if not generator.process_all_sheets(self.month):
                return {
                    'status': 'failed',
                    'message': '数据处理失败'
                }

            # 生成输出文件名
            excel_filename = f"{self.company}_{self.month}_对账单.xls"
            excel_path = os.path.join(output_dir, excel_filename)

            # 导出Excel
            if not generator.export_to_excel(excel_path):
                return {
                    'status': 'failed',
                    'message': 'Excel导出失败'
                }

            # 收集统计数据
            stats = self._collect_statistics(generator)

            return {
                'status': 'success',
                'message': f'✓ 数据处理完成，共 {len(generator.all_data)} 条记录',
                'records_count': len(generator.all_data),
                'coverage_days': stats['coverage_days'],
                'coverage_rate': stats['coverage_rate'],
                'total_debit': stats['total_debit'],
                'total_credit': stats['total_credit'],
                'balance': stats['balance'],
                'bank_details': stats['bank_details'],
                'excel_path': excel_path
            }

        except Exception as e:
            import logging
            logging.getLogger("main").error(f"Service generation error: {str(e)}", exc_info=True)
            return {
                'status': 'failed',
                'message': f'处理出错: {str(e)}'
            }



    def _collect_statistics(self, generator) -> dict:
        """
        收集统计数据

        Args:
            generator: 生成器实例

        Returns:
            dict: 统计数据
        """
        # 计算数据覆盖度
        covered_days = set()
        for data_row in generator.all_data:
            try:
                date_str = data_row['date'].replace('/', '-')
                day = int(date_str.split('-')[2])
                covered_days.add(day)
            except:
                pass

        year, month = map(int, self.month.split('-'))
        total_days = calendar.monthrange(year, month)[1]
        coverage_rate = len(covered_days) / total_days * 100 if total_days > 0 else 0

        # 计算借贷总额
        total_debit = sum(float(d['debit']) if d['debit'] else 0 for d in generator.all_data)
        total_credit = sum(float(d['credit']) if d['credit'] else 0 for d in generator.all_data)
        balance = total_debit - total_credit

        # 按银行统计
        bank_stats = {}
        for data_row in generator.all_data:
            bank_name = data_row['bank_name']
            if bank_name not in bank_stats:
                bank_stats[bank_name] = {
                    'name': bank_name,
                    'records': 0,
                    'debit': 0.0,
                    'credit': 0.0
                }

            bank_stats[bank_name]['records'] += 1
            bank_stats[bank_name]['debit'] += float(data_row['debit']) if data_row['debit'] else 0
            bank_stats[bank_name]['credit'] += float(data_row['credit']) if data_row['credit'] else 0

        return {
            'coverage_days': len(covered_days),
            'coverage_rate': coverage_rate,
            'total_debit': total_debit,
            'total_credit': total_credit,
            'balance': balance,
            'bank_details': list(bank_stats.values())
        }
