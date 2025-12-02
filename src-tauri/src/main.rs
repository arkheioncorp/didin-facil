// TikTrend Finder - Tauri Backend
// Rust backend for desktop application

#![cfg_attr(
    all(not(debug_assertions), target_os = "windows"),
    windows_subsystem = "windows"
)]

mod commands;
mod config;
mod database;
mod models;
mod scraper;

use tauri::Manager;
use std::sync::Arc;
use tokio::sync::Mutex;
use models::ScraperStatus;

// Global state for scraper status
pub struct ScraperState(pub Arc<Mutex<ScraperStatus>>);

fn main() {
    dotenv::dotenv().ok();
    
    tauri::Builder::default()
        .plugin(tauri_plugin_log::Builder::default().build())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_http::init())
        .manage(ScraperState(Arc::new(Mutex::new(ScraperStatus {
            is_running: false,
            progress: 0.0,
            current_product: None,
            products_found: 0,
            errors: vec![],
            logs: vec![],
            started_at: None,
            status_message: None,
        }))))
        .setup(|app| {
            // Initialize database
            let app_dir = app.path().app_data_dir().expect("Failed to get app data dir");
            std::fs::create_dir_all(&app_dir).ok();
            
            let db_path = app_dir.join("tiktrend.db");
            database::init_database(&db_path).expect("Failed to initialize database");
            
            log::info!("TikTrend Finder initialized successfully!");
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            // Product commands
            commands::search_products,
            commands::get_products,
            commands::get_product_by_id,
            commands::get_product_history,
            // Favorite commands
            commands::add_favorite,
            commands::remove_favorite,
            commands::get_favorites,
            commands::create_favorite_list,
            commands::get_favorite_lists,
            commands::delete_favorite_list,
            // Copy generation commands
            commands::generate_copy,
            commands::get_copy_history,
            // Dashboard & user commands
            commands::get_user_stats,
            commands::validate_license,
            // Subscription commands (SaaS Híbrido)
            commands::validate_subscription,
            commands::get_cached_subscription,
            commands::check_feature_access,
            commands::get_execution_mode,
            commands::can_work_offline,
            // Scraper commands
            commands::scrape_tiktok_shop,
            commands::get_scraper_status,
            commands::stop_scraper,
            commands::test_proxy,
            commands::sync_products,
            commands::update_selectors,
            commands::fetch_job,
            // Search history commands
            commands::save_search_history,
            commands::get_search_history,
            // Settings commands
            commands::save_settings,
            commands::get_settings,
            // Export command
            commands::export_products,
        ])
        .run(tauri::generate_context!())
        .expect("Error while running TikTrend Finder");
}

