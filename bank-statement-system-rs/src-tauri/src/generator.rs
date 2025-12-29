use std::collections::HashMap;
use serde::{Deserialize, Serialize};
use std::path::Path;
use calamine::{Reader, open_workbook_auto, Data, DataType};
use rust_xlsxwriter::Workbook;

#[derive(Debug, Serialize, Deserialize)]
pub struct ProcessResult {
    pub success: bool,
    pub message: String,
    pub records_count: usize,
    pub total_debit: f64,
    pub total_credit: f64,
    pub output_path: String,
    pub records: Vec<StatementRecord>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatementRecord {
    pub date: String,
    pub settlement_no: String,
    pub debit: f64,
    pub credit: f64,
    pub account_code: String,
    pub remark: String,
    pub bank_name: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GeneratorConfig {
    pub company_name: String,
    pub bank_mapping: HashMap<String, String>, // "招行" -> "100202"
    
    // Column indices (0-based)
    pub date_col: usize,
    pub description_col: usize, // 摘要/项目明细
    pub income_col: usize,      // 收入/借方
    pub expense_col: usize,     // 支出/贷方
    
    pub start_row: usize,       // 0-based, data starts after this row
}

impl GeneratorConfig {
    pub fn leishi_tiandi() -> Self {
        let mut mapping = HashMap::new();
        mapping.insert("建设银行".to_string(), "100202".to_string());
        mapping.insert("北苑农行".to_string(), "100221".to_string());
        mapping.insert("浦发银行".to_string(), "100218".to_string());
        mapping.insert("立水桥招行".to_string(), "100228".to_string());
        mapping.insert("媒体村交通银行".to_string(), "100217".to_string());
        mapping.insert("北苑平安7007".to_string(), "100222".to_string());
        mapping.insert("中信银行".to_string(), "100242".to_string());
        mapping.insert("兴业银行".to_string(), "100230".to_string());
        mapping.insert("民生银行".to_string(), "100232".to_string());
        mapping.insert("杭州银行".to_string(), "100234".to_string());
        mapping.insert("星展银行".to_string(), "100244".to_string());
        mapping.insert("招行保证金户".to_string(), "100241".to_string());

        Self {
            company_name: "雷石天地".to_string(),
            bank_mapping: mapping,
            date_col: 0,
            description_col: 1,
            income_col: 4,
            expense_col: 5,
            start_row: 3, // Data starts at line 4 (index 3)
        }
    }

    pub fn leihai() -> Self {
        let mut mapping = HashMap::new();
        mapping.insert("建行".to_string(), "100202".to_string());
        mapping.insert("浦发".to_string(), "100210".to_string());

        Self {
            company_name: "镭海".to_string(),
            bank_mapping: mapping,
            date_col: 0,
            description_col: 1,
            income_col: 3, // Logic from Leihai script
            expense_col: 4,
            start_row: 3,
        }
    }

    pub fn chengdu_leishi() -> Self {
        let mut mapping = HashMap::new();
        mapping.insert("中信".to_string(), "100201".to_string());
        mapping.insert("招行".to_string(), "100202".to_string());

        Self {
            company_name: "成都雷石".to_string(),
            bank_mapping: mapping,
            date_col: 0,
            description_col: 1,
            income_col: 4,
            expense_col: 5,
            start_row: 3,
        }
    }
}

pub fn process_excel<P: AsRef<Path>>(input_path: P, output_path: P, config: GeneratorConfig, target_month: &str) -> Result<ProcessResult, String> {
    let mut workbook = open_workbook_auto(input_path.as_ref()).map_err(|e| format!("无法打开Excel文件: {}", e))?;
    let sheets = workbook.sheet_names().to_owned();

    let mut all_records = Vec::new();
    let mut total_debit = 0.0;
    let mut total_credit = 0.0;

    // Parse target month (YYYY-MM)
    println!("Target Month: {}", target_month);

    for sheet_name in sheets {
        println!("Checking sheet: {}", sheet_name);
        // Find bank code
        let bank_code = match config.bank_mapping.get(&sheet_name) {
            Some(code) => code.clone(),
            None => {
                 println!("Skipping sheet '{}': Not in bank mapping", sheet_name);
                 continue; 
            }
        };

        // Try to get the range directly. In newer calamine, worksheet_range returns Result<Range<Data>, Error> usually.
        // We handle it as Result first.
        let range = workbook.worksheet_range(&sheet_name)
            .map_err(|e| format!("Error reading sheet {}: {}", sheet_name, e))?;

        for (i, row) in range.rows().enumerate() {
            if i < config.start_row { continue; }
            
            // Check bounds
            if row.len() <= config.expense_col { continue; }

            // 1. Get Date
            // 1. Get Date
            let date_cell = row.get(config.date_col);
            let date_str = if let Some(d) = date_cell.and_then(|c| c.as_date()) {
                d.to_string()
            } else if let Some(dt) = date_cell.and_then(|c| c.as_datetime()) {
                dt.date().to_string()
            } else if let Some(s) = date_cell.and_then(|c| c.as_string()) {
                s
            } else if let Some(f) = date_cell.and_then(|c| c.as_f64()) {
                 println!("Raw Float date: {}", f);
                 if let Some(d) = excel_date_to_string(f) {
                    d
                 } else {
                    f.to_string()
                 }
            } else {
                continue;
            };

            // Remove extra logic matching Data variants manually since we use helper methods

            
            // Validate date against target_month
            if !date_str.starts_with(target_month) && !date_str.contains(&target_month.replace("-", "/")) {
                println!("Row {} skipped: Date '{}' does not match target '{}'", i, date_str, target_month);
                continue;
            }
            
            println!("Match found! Date: {}", date_str);

            // 2. Get Amounts
            let income_cell = row.get(config.income_col);
            let expense_cell = row.get(config.expense_col);

            let debit = match income_cell {
                Some(Data::Float(f)) => *f,
                Some(Data::Int(i)) => *i as f64,
                _ => 0.0,
            };

            let credit = match expense_cell {
                Some(Data::Float(f)) => *f,
                Some(Data::Int(i)) => *i as f64,
                _ => 0.0,
            };

            if debit == 0.0 && credit == 0.0 { continue; }

            // 3. Get Remark
            let remark = match row.get(config.description_col) {
                Some(Data::String(s)) => s.clone(),
                _ => String::new(),
            };

            // Add to records
            all_records.push(StatementRecord {
                date: date_str,
                settlement_no: String::new(),
                debit,
                credit,
                account_code: bank_code.clone(),
                remark,
                bank_name: sheet_name.clone(),
            });

            total_debit += debit;
            total_credit += credit;
        }
    }

    if all_records.is_empty() {
        return Err("未找到符合条件的记录".to_string());
    }

    // Write to Excel
    let mut out_wb = Workbook::new();
    let worksheet = out_wb.add_worksheet();

    // Headers
    worksheet.write_string(0, 0, "日期").map_err(|e| e.to_string())?;
    worksheet.write_string(0, 1, "结算号").map_err(|e| e.to_string())?;
    worksheet.write_string(0, 2, "借方金额").map_err(|e| e.to_string())?;
    worksheet.write_string(0, 3, "贷方金额").map_err(|e| e.to_string())?;
    worksheet.write_string(0, 4, "账号（银行科目号）").map_err(|e| e.to_string())?;
    worksheet.write_string(0, 5, "备注").map_err(|e| e.to_string())?;

    for (i, record) in all_records.iter().enumerate() {
        let row = (i + 1) as u32;
        worksheet.write_string(row, 0, &record.date).map_err(|e| e.to_string())?;
        worksheet.write_string(row, 1, &record.settlement_no).map_err(|e| e.to_string())?;
        
        if record.debit != 0.0 {
            worksheet.write_number(row, 2, record.debit).map_err(|e| e.to_string())?;
        }
        if record.credit != 0.0 {
            worksheet.write_number(row, 3, record.credit).map_err(|e| e.to_string())?;
        }
        
        worksheet.write_string(row, 4, &record.account_code).map_err(|e| e.to_string())?;
        worksheet.write_string(row, 5, &record.remark).map_err(|e| e.to_string())?;
    }

    out_wb.save(output_path.as_ref()).map_err(|e| e.to_string())?;

    Ok(ProcessResult {
        success: true,
        message: format!("成功导出 {} 条记录", all_records.len()),
        records_count: all_records.len(),
        total_debit,
        total_credit,
        output_path: output_path.as_ref().to_string_lossy().to_string(),
        records: all_records,
    })
}

fn excel_date_to_string(serial: f64) -> Option<String> {
    use chrono::Duration;
    let base = chrono::NaiveDate::from_ymd_opt(1899, 12, 30)?;
    let days = serial.trunc() as i64;
    let date = base + Duration::days(days);
    Some(date.format("%Y-%m-%d").to_string())
}
