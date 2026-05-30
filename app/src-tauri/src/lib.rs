use tauri::Manager;
use std::process::Command;

// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .setup(|app| {
            // In production, the backend is bundled as an executable.
            let mut backend_path = std::env::current_exe().unwrap_or_default();
            backend_path.pop();
            backend_path.push("wildwatch_backend.exe");
            
            if backend_path.exists() {
                let _ = Command::new(backend_path).spawn();
            }
            Ok(())
        })
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![greet])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
