#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
成都雷石 - 银行对账单生成工具 v2.0

公司：成都雷石
银行账户：
  - 中信 (100201)
  - 招行 (100202)

用途：将成都雷石的银行到款明细表转换为用友系统导入格式

作者：冰雨竹
日期：2025-12-18
版本：v2.0
"""

import xlrd
import xlwt
from datetime import datetime
import calendar
import sys
import os


# ==================== 成都雷石银行配置 ====================
BANK_CODE_MAPPING = {
    '中信': '100201',
    '招行': '100202',
}

# 默认文件路径
DEFAULT_INPUT_FILE = '/Users/mi/Downloads/2025年成都雷石到款明细表 .xls'


class ChengduLeishiStatementGenerator:
    """成都雷石银行对账单生成器"""

    def __init__(self, input_file):
        """初始化生成器"""
        self.input_file = input_file
        self.workbook = None
        self.datemode = 0
        self.all_data = []
        self.errors = []
        self.warnings = []
        self.month_info = None

    def load_workbook(self):
        """加载源数据文件"""
        try:
            print(f"正在加载文件: {self.input_file}")
            self.workbook = xlrd.open_workbook(self.input_file, formatting_info=False)
            self.datemode = self.workbook.datemode
            print(f"[OK] 文件加载成功，包含 {len(self.workbook.sheet_names())} 个sheet")
            return True
        except Exception as e:
            print(f"[ERROR] 文件加载失败: {e}")
            return False

    def get_month_info(self, target_month):
        """获取月份信息（自动处理28/30/31天）"""
        if len(target_month) <= 2:
            current_year = datetime.now().year
            target_month = f"{current_year}-{target_month.zfill(2)}"

        try:
            year, month = map(int, target_month.split('-'))
            last_day = calendar.monthrange(year, month)[1]

            return {
                'year': year,
                'month': month,
                'target_month': target_month,
                'first_day': f"{year:04d}-{month:02d}-01",
                'last_day': f"{year:04d}-{month:02d}-{last_day:02d}",
                'total_days': last_day,
                'month_name': f"{year}年{month}月"
            }
        except Exception as e:
            print(f"[ERROR] 月份格式错误: {e}")
            return None

    def convert_excel_date(self, excel_date):
        """转换Excel日期格式为 YYYY/MM/DD"""
        try:
            date_tuple = xlrd.xldate_as_tuple(excel_date, self.datemode)
            return datetime(*date_tuple).strftime('%Y/%m/%d')
        except Exception as e:
            self.warnings.append(f"日期转换失败: {excel_date}")
            return None

    def is_in_target_month(self, date_str):
        """判断日期是否在目标月份内"""
        if not date_str or not self.month_info:
            return False

        try:
            date_normalized = date_str.replace('/', '-')
            first_day = self.month_info['first_day']
            last_day = self.month_info['last_day']
            return first_day <= date_normalized <= last_day
        except:
            return False

    def validate_row_data(self, row_data, row_idx):
        """验证单行数据"""
        row_errors = []
        row_warnings = []

        if not row_data.get('date'):
            row_errors.append(f"行{row_idx}: 日期为空")

        debit = row_data.get('debit', '')
        credit = row_data.get('credit', '')

        if debit:
            if not isinstance(debit, (int, float)):
                row_errors.append(f"行{row_idx}: 借方金额格式错误")
            elif debit < 0:
                row_errors.append(f"行{row_idx}: 借方金额不能为负数")
            elif debit > 50000000:
                row_warnings.append(f"行{row_idx}: 借方金额异常大 {debit:,.2f}元")

        if credit:
            if not isinstance(credit, (int, float)):
                row_errors.append(f"行{row_idx}: 贷方金额格式错误")
            elif credit < 0:
                row_errors.append(f"行{row_idx}: 贷方金额不能为负数")
            elif credit > 50000000:
                row_warnings.append(f"行{row_idx}: 贷方金额异常大 {credit:,.2f}元")

        if not row_data.get('account_code'):
            row_errors.append(f"行{row_idx}: 缺少银行编码")

        is_valid = len(row_errors) == 0
        return is_valid, row_errors, row_warnings

    def read_sheet_data(self, sheet_name):
        """读取单个银行sheet的数据"""
        try:
            sheet = self.workbook.sheet_by_name(sheet_name)
        except Exception as e:
            self.warnings.append(f"找不到sheet [{sheet_name}]: {e}")
            return []

        bank_code = BANK_CODE_MAPPING.get(sheet_name)
        if not bank_code:
            self.warnings.append(f"找不到 [{sheet_name}] 的银行编码")
            return []

        data_list = []
        skipped_count = 0
        error_count = 0

        # 成都雷石数据结构：从第4行开始（第0行标题，第1行表头，第2行期初余额，第3行开始数据）
        # 列顺序：[日期(0), 项目明细(1), 备注(2), 结算方式(3), 收入(4), 支出(5), 余额(6), 公司备注(7)]
        for row_idx in range(3, sheet.nrows):
            try:
                date_cell = sheet.cell_value(row_idx, 0)  # 日期
                account_name = sheet.cell_value(row_idx, 1)  # 项目明细
                income = sheet.cell_value(row_idx, 4)  # 收入
                expense = sheet.cell_value(row_idx, 5)  # 支出

                # 跳过期初余额行
                if '期初余额' in str(account_name):
                    continue

                # 跳过空行
                if not date_cell:
                    continue

                # 转换日期
                date_str = self.convert_excel_date(date_cell)
                if not date_str:
                    error_count += 1
                    continue

                # 筛选目标月份
                if not self.is_in_target_month(date_str):
                    skipped_count += 1
                    continue

                # 处理金额
                debit_amount = income if income else ''
                credit_amount = expense if expense else ''

                # 跳过借贷方都为空或都为0的行
                if (not debit_amount or debit_amount == 0) and (not credit_amount or credit_amount == 0):
                    skipped_count += 1
                    continue

                # 构建数据行
                data_row = {
                    'date': date_str,
                    'settlement_no': '',
                    'debit': debit_amount,
                    'credit': credit_amount,
                    'account_code': bank_code,
                    'remark': '',
                    'bank_name': sheet_name,
                    'source_row': row_idx + 1
                }

                # 验证数据
                is_valid, row_errors, row_warnings = self.validate_row_data(data_row, row_idx + 1)

                if row_errors:
                    self.errors.extend(row_errors)
                    error_count += 1
                    continue

                if row_warnings:
                    self.warnings.extend(row_warnings)

                data_list.append(data_row)

            except Exception as e:
                error_count += 1
                self.errors.append(f"[{sheet_name}] 行{row_idx + 1} 处理出错: {e}")
                continue

        print(f"  [{sheet_name}] 读取完成：匹配 {len(data_list)} 条，跳过 {skipped_count} 条，错误 {error_count} 条")
        return data_list

    def process_all_sheets(self, target_month):
        """处理所有银行sheet"""
        self.month_info = self.get_month_info(target_month)
        if not self.month_info:
            return False

        print(f"\n开始处理数据 - 成都雷石")
        print(f"目标月份: {self.month_info['month_name']} ({self.month_info['total_days']}天)")
        print(f"日期范围: {self.month_info['first_day']} ~ {self.month_info['last_day']}")
        print("=" * 60)

        self.all_data = []

        for sheet_name in BANK_CODE_MAPPING.keys():
            sheet_data = self.read_sheet_data(sheet_name)
            self.all_data.extend(sheet_data)

        print("=" * 60)
        print(f"[OK] 数据处理完成，共 {len(self.all_data)} 条有效记录")

        return True

    def check_data_quality(self):
        """检查数据质量"""
        if not self.all_data:
            return

        print("\n" + "=" * 60)
        print("数据质量检查")
        print("=" * 60)

        # 1. 检查数据覆盖度
        covered_days = set()
        for data_row in self.all_data:
            try:
                date_str = data_row['date'].replace('/', '-')
                day = int(date_str.split('-')[2])
                covered_days.add(day)
            except:
                pass

        total_days = self.month_info['total_days']
        missing_days = set(range(1, total_days + 1)) - covered_days
        coverage_rate = len(covered_days) / total_days * 100

        print(f"\n数据覆盖度:")
        print(f"  [OK] 有数据的天数: {len(covered_days)}/{total_days} 天")
        print(f"  [OK] 覆盖率: {coverage_rate:.1f}%")
        if missing_days:
            missing_str = ', '.join([f"{d}日" for d in sorted(missing_days)[:5]])
            if len(missing_days) > 5:
                missing_str += f" 等{len(missing_days)}天"
            print(f"  [WARNING] 缺少数据的日期: {missing_str}")

        # 2. 检查借贷平衡
        total_debit = sum(float(d['debit']) if d['debit'] else 0 for d in self.all_data)
        total_credit = sum(float(d['credit']) if d['credit'] else 0 for d in self.all_data)
        balance = total_debit - total_credit

        print(f"\n借贷平衡检查:")
        print(f"  借方总额: {total_debit:,.2f} 元")
        print(f"  贷方总额: {total_credit:,.2f} 元")
        print(f"  差额: {balance:,.2f} 元", end="")
        if abs(balance) < 0.01:
            print(" [OK] (平衡)")
        elif abs(balance) < 1000:
            print(" [WARNING] (基本平衡)")
        else:
            print(" [WARNING] (不平衡，请检查)")

        # 3. 错误和警告汇总
        if self.errors:
            print(f"\n[ERROR] 发现 {len(self.errors)} 个错误:")
            for error in self.errors[:5]:
                print(f"  - {error}")
            if len(self.errors) > 5:
                print(f"  ... 还有 {len(self.errors) - 5} 个错误")

        if self.warnings:
            print(f"\n[WARNING] 发现 {len(self.warnings)} 个警告:")
            for warning in self.warnings[:5]:
                print(f"  - {warning}")
            if len(self.warnings) > 5:
                print(f"  ... 还有 {len(self.warnings) - 5} 个警告")

        print("=" * 60)

    def generate_summary(self):
        """生成数据汇总报告"""
        if not self.all_data:
            return

        print("\n" + "=" * 60)
        print("数据汇总报告")
        print("=" * 60)

        bank_stats = {}
        total_debit = 0
        total_credit = 0

        for data_row in self.all_data:
            bank_name = data_row['bank_name']
            debit = data_row['debit'] if data_row['debit'] else 0
            credit = data_row['credit'] if data_row['credit'] else 0

            if bank_name not in bank_stats:
                bank_stats[bank_name] = {'count': 0, 'debit_sum': 0, 'credit_sum': 0}

            bank_stats[bank_name]['count'] += 1
            bank_stats[bank_name]['debit_sum'] += float(debit) if debit else 0
            bank_stats[bank_name]['credit_sum'] += float(credit) if credit else 0

            total_debit += float(debit) if debit else 0
            total_credit += float(credit) if credit else 0

        print(f"\n{'银行名称':<20} {'记录数':<10} {'借方合计':<15} {'贷方合计':<15}")
        print("-" * 60)
        for bank_name, stats in bank_stats.items():
            print(f"{bank_name:<20} {stats['count']:<10} {stats['debit_sum']:<15,.2f} {stats['credit_sum']:<15,.2f}")

        print("-" * 60)
        print(f"{'总计':<20} {len(self.all_data):<10} {total_debit:<15,.2f} {total_credit:<15,.2f}")
        print("=" * 60)

    def export_to_excel(self, output_file):
        """导出到Excel文件"""
        print(f"\n正在导出数据到: {output_file}")

        output_wb = xlwt.Workbook(encoding='utf-8')
        output_sheet = output_wb.add_sheet('Sheet1')

        # 定义金额格式样式：千位分隔符 + 两位小数
        money_style = xlwt.XFStyle()
        money_style.num_format_str = '#,##0.00'

        # 设置列宽
        output_sheet.col(0).width = 3000
        output_sheet.col(1).width = 3000
        output_sheet.col(2).width = 4500
        output_sheet.col(3).width = 4500
        output_sheet.col(4).width = 5000
        output_sheet.col(5).width = 6000

        # 写入表头
        headers = ['日期', '结算号', '借方金额', '贷方金额', '账号（银行科目号）', '备注']
        for col_idx, header in enumerate(headers):
            output_sheet.write(0, col_idx, header)

        # 写入数据
        for row_idx, data_row in enumerate(self.all_data, start=1):
            output_sheet.write(row_idx, 0, data_row['date'])
            output_sheet.write(row_idx, 1, data_row['settlement_no'])

            if data_row['debit']:
                output_sheet.write(row_idx, 2, data_row['debit'], money_style)
            else:
                output_sheet.write(row_idx, 2, data_row['debit'])

            if data_row['credit']:
                output_sheet.write(row_idx, 3, data_row['credit'], money_style)
            else:
                output_sheet.write(row_idx, 3, data_row['credit'])

            output_sheet.write(row_idx, 4, data_row['account_code'])
            output_sheet.write(row_idx, 5, data_row['remark'])

        try:
            output_wb.save(output_file)
            print(f"[OK] 文件导出成功: {output_file}")
            print(f"  共导出 {len(self.all_data)} 条记录")
            return True
        except Exception as e:
            print(f"[ERROR] 文件导出失败: {e}")
            return False


def main():
    """主程序"""
    print("=" * 60)
    print("成都雷石 - 银行对账单生成工具 v2.0")
    print("=" * 60)

    # 默认参数
    default_input = DEFAULT_INPUT_FILE
    default_month = "2025-11"
    default_output = "/Users/mi/Desktop/财务/成都雷石_2025年11月_对账单.xls"

    # 获取参数
    if len(sys.argv) >= 3:
        input_file = sys.argv[1]
        target_month = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) >= 4 else None
    else:
        input_file = default_input
        target_month = default_month
        output_file = default_output
        print(f"\n使用默认参数:")
        print(f"  输入文件: {input_file}")
        print(f"  目标月份: {target_month}")
        print(f"  输出文件: {output_file}\n")

    # 自动生成输出文件名
    if not output_file:
        month_str = target_month.replace('-', '年') + '月'
        output_file = f"/Users/mi/Desktop/财务/成都雷石_{month_str}_对账单.xls"

    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        print(f"[ERROR] 错误：输入文件不存在: {input_file}")
        return

    # 创建生成器
    generator = ChengduLeishiStatementGenerator(input_file)

    # 加载文件
    if not generator.load_workbook():
        return

    # 处理数据
    if not generator.process_all_sheets(target_month):
        return

    # 数据质量检查
    generator.check_data_quality()

    # 生成汇总报告
    generator.generate_summary()

    # 导出文件
    if generator.export_to_excel(output_file):
        print(f"\n[OK] 处理完成！")
        print(f"[OK] 可以将生成的文件导入到用友系统中")
    else:
        print(f"\n[ERROR] 处理失败！")


if __name__ == "__main__":
    main()
