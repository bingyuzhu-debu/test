use rusqlite::{Connection, Result};
use tauri::Manager;

pub fn init_db(app_handle: &tauri::AppHandle) -> Result<(), String> {
    let app_dir = app_handle.path().app_data_dir().map_err(|e| e.to_string())?;
    
    // Ensure app data directory exists
    if !app_dir.exists() {
        std::fs::create_dir_all(&app_dir).map_err(|e| e.to_string())?;
    }

    let db_path = app_dir.join("history.db");
    
    let conn = Connection::open(db_path).map_err(|e| e.to_string())?;

    conn.execute(
        "CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY,
            company TEXT NOT NULL,
            month TEXT NOT NULL,
            filename TEXT NOT NULL,
            records_count INTEGER,
            total_debit REAL,
            total_credit REAL,
            records_json TEXT, -- Store full records as JSON
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )",
        [],
    ).map_err(|e| e.to_string())?;

    // Migration: Attempt to add records_json column if it doesn't exist
    // This is a simple way to handle schema evolution for this app
    let _ = conn.execute("ALTER TABLE history ADD COLUMN records_json TEXT", []);

    Ok(())
}

#[derive(serde::Serialize)]
pub struct HistoryRecord {
    pub id: i64,
    pub company: String,
    pub month: String,
    pub filename: String,
    pub records_count: i64,
    pub total_debit: f64,
    pub total_credit: f64,
    pub created_at: String,
    // records_json is internal, we usually don't return it in the list view to save bandwidth
    // but we will return it in get_history_details
    #[serde(skip_serializing_if = "Option::is_none")]
    pub records: Option<Vec<crate::generator::StatementRecord>>,
}

pub fn get_history(app_handle: &tauri::AppHandle) -> Result<Vec<HistoryRecord>, String> {
    let app_dir = app_handle.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("history.db");
    let conn = Connection::open(db_path).map_err(|e| e.to_string())?;

    let mut stmt = conn.prepare(
        "SELECT id, company, month, filename, records_count, total_debit, total_credit, created_at FROM history ORDER BY created_at DESC LIMIT 50"
    ).map_err(|e| e.to_string())?;

    let history_iter = stmt.query_map([], |row| {
        Ok(HistoryRecord {
            id: row.get(0)?,
            company: row.get(1)?,
            month: row.get(2)?,
            filename: row.get(3)?,
            records_count: row.get(4)?,
            total_debit: row.get(5)?,
            total_credit: row.get(6)?,
            created_at: row.get(7)?,
            records: None, // No heavy details in list view
        })
    }).map_err(|e| e.to_string())?;

    let mut history = Vec::new();
    for record in history_iter {
        history.push(record.map_err(|e| e.to_string())?);
    }

    Ok(history)
}

pub fn get_history_details(app_handle: &tauri::AppHandle, id: i64) -> Result<HistoryRecord, String> {
    let app_dir = app_handle.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("history.db");
    let conn = Connection::open(db_path).map_err(|e| e.to_string())?;

    let mut stmt = conn.prepare(
        "SELECT id, company, month, filename, records_count, total_debit, total_credit, created_at, records_json FROM history WHERE id = ?1"
    ).map_err(|e| e.to_string())?;

    let record = stmt.query_row([id], |row| {
        let json_str: Option<String> = row.get(8)?;
        let records = if let Some(s) = json_str {
            serde_json::from_str(&s).unwrap_or(Some(Vec::new()))
        } else {
            None
        };

        Ok(HistoryRecord {
            id: row.get(0)?,
            company: row.get(1)?,
            month: row.get(2)?,
            filename: row.get(3)?,
            records_count: row.get(4)?,
            total_debit: row.get(5)?,
            total_credit: row.get(6)?,
            created_at: row.get(7)?,
            records,
        })
    }).map_err(|e| e.to_string())?;

    Ok(record)
}

pub fn delete_history(app_handle: &tauri::AppHandle, id: i64) -> Result<(), String> {
    let app_dir = app_handle.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("history.db");
    let conn = Connection::open(db_path).map_err(|e| e.to_string())?;

    conn.execute(
        "DELETE FROM history WHERE id = ?1",
        [id],
    ).map_err(|e| e.to_string())?;

    Ok(())
}
