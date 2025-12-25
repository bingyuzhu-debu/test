"""
工具函数
CSV和PDF导出功能
"""

import xlrd
import csv
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os


def export_to_csv(excel_path: str, csv_path: str) -> bool:
    """
    将Excel文件转换为CSV格式

    Args:
        excel_path: Excel文件路径
        csv_path: 输出CSV文件路径

    Returns:
        bool: 是否成功
    """
    try:
        # 打开Excel文件
        workbook = xlrd.open_workbook(excel_path)
        sheet = workbook.sheet_by_index(0)  # 读取第一个sheet

        # 写入CSV
        with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)

            # 逐行写入
            for row_idx in range(sheet.nrows):
                row_data = []
                for col_idx in range(sheet.ncols):
                    cell_value = sheet.cell_value(row_idx, col_idx)
                    row_data.append(str(cell_value))
                writer.writerow(row_data)

        print(f"✓ CSV文件导出成功: {csv_path}")
        return True

    except Exception as e:
        print(f"✗ CSV导出失败: {str(e)}")
        return False


def export_to_pdf(excel_path: str, pdf_path: str, company: str, month: str) -> bool:
    """
    将Excel文件转换为PDF格式（简化版，不使用中文字体）

    Args:
        excel_path: Excel文件路径
        pdf_path: 输出PDF文件路径
        company: 公司名称
        month: 月份

    Returns:
        bool: 是否成功
    """
    try:
        # 打开Excel文件
        workbook = xlrd.open_workbook(excel_path)
        sheet = workbook.sheet_by_index(0)

        # 创建PDF文档（横向A4）
        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=landscape(A4),
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            leftMargin=0.5*inch,
            rightMargin=0.5*inch
        )

        # 准备内容
        elements = []

        # 添加简单的标题（使用Spacer代替Paragraph避免中文问题）
        elements.append(Spacer(1, 0.3*inch))

        # 读取Excel数据
        data = []
        for row_idx in range(sheet.nrows):
            row_data = []
            for col_idx in range(sheet.ncols):
                cell_value = sheet.cell_value(row_idx, col_idx)
                # 转换为字符串
                if isinstance(cell_value, float):
                    # 如果是数字，格式化为两位小数
                    if cell_value.is_integer():
                        cell_value = str(int(cell_value))
                    else:
                        cell_value = f"{cell_value:.2f}"
                else:
                    cell_value = str(cell_value)
                row_data.append(cell_value)
            data.append(row_data)

        # 创建表格
        if data:
            # 计算列宽（根据列数动态调整）
            col_count = len(data[0])
            available_width = landscape(A4)[0] - 1*inch  # 总可用宽度
            col_widths = [available_width / col_count] * col_count

            table = Table(data, colWidths=col_widths)

            # 表格样式
            table_style = TableStyle([
                # 表头样式
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

                # 数据行样式
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),

                # 网格
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),

                # 隔行变色
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.lightgrey]),
            ])

            table.setStyle(table_style)
            elements.append(table)

        # 生成PDF
        doc.build(elements)

        print(f"✓ PDF文件导出成功: {pdf_path}")
        return True

    except Exception as e:
        print(f"✗ PDF导出失败: {str(e)}")
        return False


def format_currency(amount: float) -> str:
    """
    格式化金额（千位分隔符）

    Args:
        amount: 金额

    Returns:
        str: 格式化后的字符串
    """
    return f"{amount:,.2f}"


def validate_month(month: str) -> bool:
    """
    验证月份格式是否正确

    Args:
        month: 月份字符串（YYYY-MM）

    Returns:
        bool: 是否有效
    """
    from datetime import datetime

    try:
        datetime.strptime(month, '%Y-%m')
        return True
    except ValueError:
        return False


def validate_excel_file(file_path: str) -> bool:
    """
    验证Excel文件是否有效

    Args:
        file_path: 文件路径

    Returns:
        bool: 是否有效
    """
    if not os.path.exists(file_path):
        return False

    if not file_path.endswith(('.xls', '.xlsx')):
        return False

    try:
        xlrd.open_workbook(file_path)
        return True
    except:
        return False
