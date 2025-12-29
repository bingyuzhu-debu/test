// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

mod db;
mod generator;
use generator::{GeneratorConfig, process_excel};
use std::path::PathBuf;
use tauri::Manager; // Import Manager trait for .path()

#[tauri::command]
async fn generate_statement(app: tauri::AppHandle, company: String, month: String, file_path: String) -> Result<generator::ProcessResult, String> {
    let config = match company.as_str() {
        "雷石天地" => GeneratorConfig::leishi_tiandi(),
        "镭海" => GeneratorConfig::leihai(),
        "成都雷石" => GeneratorConfig::chengdu_leishi(),
        _ => return Err(format!("不支持的公司: {}", company)),
    };

    let input_path = PathBuf::from(&file_path);
    let parent = input_path.parent().unwrap_or(std::path::Path::new(""));
    let output_name = format!("{}_{}_对账单.xlsx", company, month);
    let output_path = parent.join(output_name);

    let result = process_excel(&input_path, &output_path, config, &month)?;

    if result.success {
        if let Err(e) = save_history(&app, &company, &month, &file_path, &result) {
            eprintln!("Failed to save history: {}", e);
        }
    }

    Ok(result)
}

fn save_history(app: &tauri::AppHandle, company: &str, month: &str, filename: &str, result: &generator::ProcessResult) -> Result<(), String> {
    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("history.db");
    let conn = rusqlite::Connection::open(db_path).map_err(|e| e.to_string())?;

    let records_json = serde_json::to_string(&result.records).map_err(|e| e.to_string())?;

    conn.execute(
        "INSERT INTO history (company, month, filename, records_count, total_debit, total_credit, records_json) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7)",
        rusqlite::params![company, month, filename, result.records_count as i64, result.total_debit, result.total_credit, records_json],
    ).map_err(|e| e.to_string())?;

    Ok(())
}

#[tauri::command]
fn get_history(app: tauri::AppHandle) -> Result<Vec<db::HistoryRecord>, String> {
    db::get_history(&app)
}

#[tauri::command]
fn get_history_details(app: tauri::AppHandle, id: i64) -> Result<db::HistoryRecord, String> {
    db::get_history_details(&app, id)
}

#[tauri::command]
fn delete_history(app: tauri::AppHandle, id: i64) -> Result<(), String> {
    db::delete_history(&app, id)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .setup(|app| {
            if let Err(e) = db::init_db(app.handle()) {
                eprintln!("Error initializing database: {}", e);
            }
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![greet, generate_statement, get_history, get_history_details, delete_history])

        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
