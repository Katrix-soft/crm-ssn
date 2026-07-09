#![cfg_attr(
  all(not(debug_assertions), target_os = "windows"),
  windows_subsystem = "windows"
)]

use std::process::{Command, Child, Stdio};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;

fn main() {
    let child_process: Arc<Mutex<Option<Child>>> = Arc::new(Mutex::new(None));
    let child_process_clone = Arc::clone(&child_process);

    // Spawn Python FastAPI server in a background thread
    thread::spawn(move || {
        let possible_pythons = vec![
            "/home/nachin/Documentos/katrix/productor de seguros/.venv/bin/python",
            "/home/nachin/Documentos/katrix/pas/backend/venv/bin/python",
            "/home/nachin/Documentos/katrix/katrix-rag/backend/venv/bin/python",
            "python3",
            "python"
        ];

        let api_dir = "/home/nachin/Documentos/katrix/productor de seguros/api-crm";
        let env_file = "/home/nachin/Documentos/katrix/productor de seguros/api-crm/.env";

        let mut spawned = false;

        for python_path in possible_pythons {
            println!("🔍 Probing Python interpreter: {}", python_path);
            let check = Command::new(python_path)
                .args(&["-c", "import fastapi, uvicorn"])
                .current_dir(api_dir)
                .status();

            if let Ok(status) = check {
                if status.success() {
                    println!("🚀 Found functional Python virtual environment with FastAPI: {}", python_path);
                    let mut cmd = Command::new(python_path);
                    cmd.args(&[
                        "-m", "uvicorn", 
                        "api:app", 
                        "--host", "127.0.0.1", 
                        "--port", "8000",
                        "--env-file", env_file
                    ])
                    .current_dir(api_dir)
                    .stdout(Stdio::inherit())
                    .stderr(Stdio::inherit());

                    match cmd.spawn() {
                        Ok(child) => {
                            println!("✅ FastAPI backend spawned successfully!");
                            let mut lock = child_process_clone.lock().unwrap();
                            *lock = Some(child);
                            spawned = true;
                            break;
                        }
                        Err(e) => {
                            println!("❌ Failed to spawn Python child process: {}", e);
                        }
                    }
                }
            }
        }

        if !spawned {
            eprintln!("⚠️ WARNING: No Python virtual environment with FastAPI and Uvicorn was found to launch the backend automatically.");
        }
    });

    tauri::Builder::default()
        .on_window_event(move |_window, event| {
            if let tauri::WindowEvent::Destroyed = event {
                let mut lock = child_process.lock().unwrap();
                if let Some(mut child) = lock.take() {
                    println!("🛑 Tauri window closed. Terminating Python FastAPI backend child process...");
                    let _ = child.kill();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
