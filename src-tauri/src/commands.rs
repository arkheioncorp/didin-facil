// Tauri commands - API for frontend
use crate::config::{AppSettings, ScraperConfig};
use crate::database;
use crate::models::*;
use crate::scraper::TikTokScraper;
use crate::ScraperState;
use chrono::Utc;
use serde::{Deserialize, Serialize};
use serde_json::json;
use sha2::{Digest, Sha256};
use std::fs;
use sysinfo::{Disks, Networks, System};
use tauri::{command, AppHandle, Manager, State};
use ts_rs::TS;

const API_URL: &str = "http://localhost:8000";

fn get_hardware_id() -> String {
    let mut sys = System::new_all();
    sys.refresh_all();

    let cpu_id = sys
        .cpus()
        .iter()
        .map(|cpu| cpu.brand())
        .collect::<Vec<_>>()
        .join("");

    let networks = Networks::new_with_refreshed_list();
    let mac_addresses = networks
        .iter()
        .map(|(_, data)| data.mac_address().to_string())
        .collect::<Vec<_>>()
        .join("");

    let mut hasher = Sha256::new();
    hasher.update(cpu_id.as_bytes());
    hasher.update(mac_addresses.as_bytes());
    let hash = hasher.finalize();

    format!("{:x}", hash)
}

/// Search products with filters
#[command]
pub async fn search_products(
    app: AppHandle,
    filters: SearchFilters,
) -> Result<PaginatedResponse<Product>, String> {
    log::info!("Searching products with filters: {:?}", filters);

    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");

    let result = database::search_products(&db_path, &filters)
        .map_err(|e| format!("Database error: {}", e))?;

    Ok(result)
}

/// Get paginated products
#[command]
pub async fn get_products(
    app: AppHandle,
    page: Option<i32>,
    page_size: Option<i32>,
) -> Result<PaginatedResponse<Product>, String> {
    let page = page.unwrap_or(1);
    let page_size = page_size.unwrap_or(20);

    log::info!("Getting products page {} with size {}", page, page_size);

    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");

    let filters = SearchFilters {
        query: None,
        categories: vec![],
        price_min: None,
        price_max: None,
        sales_min: None,
        rating_min: None,
        has_free_shipping: None,
        is_trending: None,
        is_on_sale: None,
        sort_by: Some("collected_at".to_string()),
        sort_order: Some("DESC".to_string()),
        page: Some(page),
        page_size: Some(page_size),
    };

    database::search_products(&db_path, &filters).map_err(|e| format!("Database error: {}", e))
}

/// Get single product by ID
#[command]
pub async fn get_product_by_id(app: AppHandle, id: String) -> Result<Option<Product>, String> {
    log::info!("Getting product by id: {}", id);

    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");

    database::get_product_by_id(&db_path, &id).map_err(|e| format!("Database error: {}", e))
}

/// Add product to favorites
#[command]
pub async fn add_favorite(
    app: AppHandle,
    product_id: String,
    list_id: Option<String>,
    notes: Option<String>,
) -> Result<FavoriteItem, String> {
    log::info!("Adding favorite: {} to list {:?}", product_id, list_id);

    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");

    // Default user_id for desktop (single user)
    let user_id = "default_user".to_string();

    database::add_favorite(
        &db_path,
        &user_id,
        &product_id,
        list_id.as_deref(),
        notes.as_deref(),
    )
    .map_err(|e| format!("Database error: {}", e))
}

/// Remove product from favorites
#[command]
pub async fn remove_favorite(app: AppHandle, product_id: String) -> Result<bool, String> {
    log::info!("Removing favorite: {}", product_id);

    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");

    let user_id = "default_user".to_string();

    database::remove_favorite(&db_path, &user_id, &product_id)
        .map_err(|e| format!("Database error: {}", e))
}

/// Get all favorites with product data
#[command]
pub async fn get_favorites(
    app: AppHandle,
    list_id: Option<String>,
) -> Result<Vec<FavoriteWithProduct>, String> {
    log::info!("Getting favorites for list: {:?}", list_id);

    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");

    let user_id = "default_user".to_string();

    database::get_favorites(&db_path, &user_id, list_id.as_deref())
        .map_err(|e| format!("Database error: {}", e))
}

/// Create favorite list
#[command]
pub async fn create_favorite_list(
    app: AppHandle,
    name: String,
    description: Option<String>,
    color: Option<String>,
    icon: Option<String>,
) -> Result<FavoriteList, String> {
    log::info!("Creating favorite list: {}", name);

    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");

    let user_id = "default_user".to_string();

    database::create_favorite_list(
        &db_path,
        &user_id,
        &name,
        description.as_deref(),
        color.as_deref(),
        icon.as_deref(),
    )
    .map_err(|e| format!("Database error: {}", e))
}

/// Get all favorite lists
#[command]
pub async fn get_favorite_lists(app: AppHandle) -> Result<Vec<FavoriteList>, String> {
    log::info!("Getting favorite lists");

    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");

    let user_id = "default_user".to_string();

    database::get_favorite_lists(&db_path, &user_id).map_err(|e| format!("Database error: {}", e))
}

/// Delete favorite list
#[command]
pub async fn delete_favorite_list(app: AppHandle, list_id: String) -> Result<bool, String> {
    log::info!("Deleting favorite list: {}", list_id);

    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");

    database::delete_favorite_list(&db_path, &list_id).map_err(|e| format!("Database error: {}", e))
}

/// Generate AI copy for product
#[command]
pub async fn generate_copy(app: AppHandle, request: CopyRequest) -> Result<CopyResponse, String> {
    log::info!("Generating copy for product: {}", request.product_id);

    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");

    // Get product data for context
    let product = database::get_product_by_id(&db_path, &request.product_id)
        .map_err(|e| format!("Database error: {}", e))?
        .ok_or("Product not found")?;

    // Try to call API first
    let client = reqwest::Client::new();
    let api_payload = json!({
        "product_id": product.id,
        "product_title": product.title,
        "product_description": product.description,
        "product_price": product.price,
        "copy_type": request.copy_type,
        "tone": request.tone,
        "platform": "instagram",
        "language": "pt-BR"
    });

    let copy_content = match client
        .post(format!("{}/copy/generate", API_URL))
        .json(&api_payload)
        .send()
        .await
    {
        Ok(response) => {
            if response.status().is_success() {
                let api_response: serde_json::Value = response
                    .json()
                    .await
                    .map_err(|e| format!("Failed to parse API response: {}", e))?;

                api_response["copy_text"]
                    .as_str()
                    .unwrap_or_else(|| "Error: Empty response from AI")
                    .to_string()
            } else if response.status() == reqwest::StatusCode::TOO_MANY_REQUESTS
                || response.status() == reqwest::StatusCode::FORBIDDEN
            {
                return Err("QUOTA_EXCEEDED".to_string());
            } else {
                log::warn!(
                    "API error: {}, falling back to local template",
                    response.status()
                );
                generate_copy_content(&product, &request.copy_type, &request.tone)
            }
        }
        Err(e) => {
            log::warn!("API request failed: {}, falling back to local template", e);
            generate_copy_content(&product, &request.copy_type, &request.tone)
        }
    };

    // Save to history
    let user_id = "default_user".to_string();
    database::save_copy_history(
        &db_path,
        &user_id,
        Some(&request.product_id),
        &request.copy_type,
        &request.tone,
        &copy_content,
        0,
    )
    .ok();

    Ok(CopyResponse {
        content: copy_content,
        tokens_used: 0,
    })
}

/// Get copy history
#[command]
pub async fn get_copy_history(
    app: AppHandle,
    limit: Option<i32>,
) -> Result<Vec<CopyHistory>, String> {
    log::info!("Getting copy history");

    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");

    let user_id = "default_user".to_string();

    database::get_copy_history(&db_path, &user_id, limit.unwrap_or(50))
        .map_err(|e| format!("Database error: {}", e))
}

/// Get dashboard statistics
#[command]
pub async fn get_user_stats(app: AppHandle) -> Result<DashboardStats, String> {
    log::info!("Getting user stats");

    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");

    let user_id = "default_user".to_string();

    database::get_dashboard_stats(&db_path, &user_id).map_err(|e| format!("Database error: {}", e))
}

/// Validate license
#[command]
pub async fn validate_license(license_key: String) -> Result<License, String> {
    log::info!("Validating license: {}", license_key);

    let hwid = get_hardware_id();
    let client = reqwest::Client::new();

    let api_payload = json!({
        "email": license_key,
        "hwid": hwid,
        "app_version": "1.0.0"
    });

    match client
        .post(format!("{}/license/validate", API_URL))
        .json(&api_payload)
        .send()
        .await
    {
        Ok(response) => {
            if response.status().is_success() {
                let api_response: serde_json::Value = response
                    .json()
                    .await
                    .map_err(|e| format!("Failed to parse API response: {}", e))?;

                let features = api_response["features"]
                    .as_object()
                    .ok_or("Invalid features format")?;

                Ok(License {
                    is_valid: api_response["valid"].as_bool().unwrap_or(false),
                    plan: api_response["plan"].as_str().unwrap_or("lifetime").to_string(),
                    features: PlanFeatures {
                        searches_unlimited: features
                            .get("searches_unlimited")
                            .and_then(|v| v.as_bool())
                            .unwrap_or(true),  // Lifetime = unlimited
                        favorites_unlimited: features
                            .get("favorites_unlimited")
                            .and_then(|v| v.as_bool())
                            .unwrap_or(true),  // Lifetime = unlimited
                        export_enabled: features
                            .get("export_enabled")
                            .and_then(|v| v.as_bool())
                            .unwrap_or(true),
                        scheduler_enabled: features
                            .get("scheduler_enabled")
                            .and_then(|v| v.as_bool())
                            .unwrap_or(true),
                    },
                    expires_at: api_response["expires_at"]
                        .as_str()
                        .unwrap_or("")
                        .to_string(),
                    credits: api_response["credits"]
                        .as_i64()
                        .unwrap_or(0) as i32,
                })
            } else {
                // Fallback to trial if API fails (e.g. 404, 500)
                // But if 403/401 it means invalid.
                // For development, let's fallback to trial if connection fails
                log::warn!("License API error: {}", response.status());
                Err(format!("License validation failed: {}", response.status()))
            }
        }
        Err(e) => {
            log::warn!("License API connection failed: {}", e);
            // Fallback to trial for offline dev
            Ok(License {
                is_valid: true,
                plan: String::from("trial (offline)"),
                features: PlanFeatures {
                    searches_unlimited: true,
                    favorites_unlimited: true,
                    export_enabled: true,
                    scheduler_enabled: false,
                },
                expires_at: chrono::Utc::now()
                    .checked_add_signed(chrono::Duration::days(7))
                    .unwrap()
                    .to_rfc3339(),
                credits: 10,  // Trial credits
            })
        }
    }
}

fn check_disk_space(path: &std::path::Path) -> Result<(), String> {
    let disks = Disks::new_with_refreshed_list();
    for disk in &disks {
        if path.starts_with(disk.mount_point()) {
            if disk.available_space() < 1_000_000_000 {
                return Err(
                    "Espaço em disco insuficiente (< 1GB). Libere espaço para continuar."
                        .to_string(),
                );
            }
        }
    }
    Ok(())
}

/// Start TikTok Shop scraper
#[command]
pub async fn scrape_tiktok_shop(
    app: AppHandle,
    config: ScraperConfig,
    state: State<'_, ScraperState>,
) -> Result<Vec<Product>, String> {
    log::info!("Starting TikTok Shop scraper with config: {:?}", config);

    // Update state to running
    {
        let mut status = state.0.lock().await;
        status.is_running = true;
        status.progress = 0.0;
        status.products_found = 0;
        status.errors.clear();
        status.started_at = Some(Utc::now().to_rfc3339());
    }

    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;

    if let Err(e) = check_disk_space(&app_dir) {
        let mut status = state.0.lock().await;
        status.is_running = false;
        status.errors.push(e.clone());
        return Err(e);
    }

    let db_path = app_dir.join("tiktrend.db");

    // Convert config to scraper config
    let mut scraper_config = crate::scraper::models::ScraperConfig::from(config);

    // Set user data path for session persistence
    let user_data = app_dir.join("browser_data");
    scraper_config.user_data_path = Some(user_data.to_string_lossy().to_string());
    scraper_config.db_path = Some(db_path.to_string_lossy().to_string());

    // Load selectors from file
    let selectors_path = app_dir.join("selectors.json");
    if selectors_path.exists() {
        if let Ok(content) = fs::read_to_string(selectors_path) {
            if let Ok(selectors) = serde_json::from_str::<Vec<String>>(&content) {
                scraper_config.selectors = Some(selectors);
            }
        }
    }

    let scraper = TikTokScraper::new(scraper_config, state.0.clone(), Some(app.clone()));
    let products = scraper.start().await.map_err(|e| e.to_string())?;

    // Save products to database
    for product in &products {
        database::save_product(&db_path, product).ok();
    }

    // Update status to completed
    {
        let mut status = state.0.lock().await;
        status.is_running = false;
        status.progress = 100.0;
        status.products_found = products.len() as i32;
    }

    log::info!("Scraper completed. Found {} products", products.len());

    Ok(products)
}

/// Get scraper status
#[command]
pub async fn get_scraper_status(state: State<'_, ScraperState>) -> Result<ScraperStatus, String> {
    let status = state.0.lock().await;
    Ok(status.clone())
}

/// Stop running scraper
#[command]
pub async fn stop_scraper(state: State<'_, ScraperState>) -> Result<bool, String> {
    let mut status = state.0.lock().await;
    if status.is_running {
        status.is_running = false;
        log::info!("Scraper stopped by user");
        Ok(true)
    } else {
        Ok(false)
    }
}

/// Save search to history
#[command]
pub async fn save_search_history(
    app: AppHandle,
    query: String,
    filters: String,
    results_count: i32,
) -> Result<bool, String> {
    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");

    let user_id = "default_user".to_string();

    database::save_search_history(&db_path, &user_id, &query, &filters, results_count)
        .map_err(|e| format!("Database error: {}", e))
}

/// Get search history
#[command]
pub async fn get_search_history(
    app: AppHandle,
    limit: Option<i32>,
) -> Result<Vec<SearchHistoryItem>, String> {
    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");

    let user_id = "default_user".to_string();

    database::get_search_history(&db_path, &user_id, limit.unwrap_or(20))
        .map_err(|e| format!("Database error: {}", e))
}

/// Save app settings
#[command]
pub async fn save_settings(app: AppHandle, settings: AppSettings) -> Result<(), String> {
    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let config_path = app_dir.join("settings.json");

    let content = serde_json::to_string_pretty(&settings).map_err(|e| e.to_string())?;
    fs::write(config_path, content).map_err(|e| e.to_string())?;

    Ok(())
}

/// Get app settings
#[command]
pub async fn get_settings(app: AppHandle) -> Result<AppSettings, String> {
    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let config_path = app_dir.join("settings.json");

    if !config_path.exists() {
        return Ok(AppSettings::default());
    }

    let content = fs::read_to_string(config_path).map_err(|e| e.to_string())?;
    let settings: AppSettings = serde_json::from_str(&content).unwrap_or_default();

    Ok(settings)
}

/// Export products to file
#[command]
pub async fn export_products(
    app: AppHandle,
    product_ids: Vec<String>,
    format: String,
    path: String,
) -> Result<String, String> {
    log::info!(
        "Exporting {} products to {} as {}",
        product_ids.len(),
        path,
        format
    );

    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");

    // Get products
    let mut products = Vec::new();
    for id in product_ids {
        if let Ok(Some(product)) = database::get_product_by_id(&db_path, &id) {
            products.push(product);
        }
    }

    // Export based on format
    let output = match format.as_str() {
        "csv" => export_to_csv(&products)?,
        "json" => serde_json::to_string_pretty(&products).map_err(|e| e.to_string())?,
        _ => return Err("Unsupported format".to_string()),
    };

    // Write to file
    std::fs::write(&path, &output).map_err(|e| e.to_string())?;

    Ok(path)
}

/// Test proxy connection
#[command]
pub async fn test_proxy(proxy: String) -> Result<bool, String> {
    log::info!("Testing proxy: {}", proxy);

    let client = reqwest::Client::builder()
        .proxy(reqwest::Proxy::all(&proxy).map_err(|e| e.to_string())?)
        .timeout(std::time::Duration::from_secs(10))
        .build()
        .map_err(|e| e.to_string())?;

    let res = client
        .get("https://api.ipify.org?format=json")
        .send()
        .await
        .map_err(|e| e.to_string())?;

    Ok(res.status().is_success())
}

/// Sync products with backend
#[command]
pub async fn sync_products(app: AppHandle) -> Result<i32, String> {
    log::info!("Syncing products with backend...");
    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");

    // Get all products
    let filters = SearchFilters {
        page_size: Some(1000), // Batch size
        ..Default::default()
    };

    let result = database::search_products(&db_path, &filters).map_err(|e| e.to_string())?;

    if result.data.is_empty() {
        return Ok(0);
    }

    let client = reqwest::Client::new();
    let res = client
        .post(format!("{}/api/products/batch", API_URL))
        .json(&result.data)
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if res.status().is_success() {
        log::info!("Synced {} products", result.data.len());
        Ok(result.data.len() as i32)
    } else {
        Err(format!("Sync failed: {}", res.status()))
    }
}

/// Update scraper selectors
#[command]
pub async fn update_selectors(app: AppHandle, selectors: Vec<String>) -> Result<(), String> {
    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let selectors_path = app_dir.join("selectors.json");
    let content = serde_json::to_string(&selectors).map_err(|e| e.to_string())?;
    fs::write(selectors_path, content).map_err(|e| e.to_string())?;
    Ok(())
}

#[derive(serde::Serialize, serde::Deserialize)]
pub struct Job {
    pub id: String,
    pub config: ScraperConfig,
}

/// Fetch pending job from backend
#[command]
pub async fn fetch_job() -> Result<Option<Job>, String> {
    let client = reqwest::Client::new();
    let res = client
        .get(format!("{}/api/jobs/pending", API_URL))
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if res.status().is_success() {
        let job = res.json::<Job>().await.map_err(|e| e.to_string())?;
        Ok(Some(job))
    } else {
        Ok(None)
    }
}

/// Get product history
#[command]
pub async fn get_product_history(
    app: AppHandle,
    id: String,
) -> Result<Vec<ProductHistory>, String> {
    log::info!("Getting history for product: {}", id);

    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");

    database::get_product_history(&db_path, &id).map_err(|e| format!("Database error: {}", e))
}

// Helper function to generate copy content
fn generate_copy_content(product: &Product, copy_type: &str, tone: &str) -> String {
    let emoji_fire = if tone == "urgent" { "🔥" } else { "" };
    let emoji_star = "⭐";
    let emoji_cart = "🛒";

    match copy_type {
        "tiktok_hook" => format!(
            "{} VOCÊ PRECISA VER ISSO!\n\n{} está BOMBANDO no TikTok!\n\n✅ {} vendidos\n✅ Avaliação {:.1}/5 {}\n✅ {}\n\nPor apenas R${:.2} 😱\n\n👇 Link na bio\n#tiktokmademebuyit #achados #compras",
            emoji_fire,
            product.title,
            product.sales_count,
            product.product_rating.unwrap_or(4.5),
            emoji_star,
            if product.has_free_shipping { "FRETE GRÁTIS!" } else { "Entrega rápida" },
            product.price
        ),
        "facebook_ad" => format!(
            "🎯 {} {}\n\n{}\n\n✨ Benefícios:\n• Alta qualidade garantida\n• {} avaliações positivas\n• {} vendidos e contando!\n\n💰 De R${:.2} por apenas R${:.2}\n{}\n\n🔗 Clique em \"Saiba Mais\" e aproveite!\n\n#dropshipping #ofertas #promocao",
            emoji_fire,
            product.title,
            product.description.as_deref().unwrap_or("O produto que você estava procurando!"),
            product.reviews_count,
            product.sales_count,
            product.original_price.unwrap_or(product.price * 1.5),
            product.price,
            if product.has_free_shipping { "🚚 FRETE GRÁTIS!" } else { "" }
        ),
        "product_description" => format!(
            "{}\n\n📦 Descrição do Produto\n\n{}\n\n⭐ Avaliação: {:.1}/5 ({} avaliações)\n{} {} vendas\n\n💲 Preço: R${:.2}\n{}\n\n🏪 Vendedor: {} (Nota: {:.1})\n\n✅ {} em estoque",
            product.title,
            product.description.as_deref().unwrap_or("Produto de alta qualidade importado."),
            product.product_rating.unwrap_or(4.5),
            product.reviews_count,
            emoji_cart,
            product.sales_count,
            product.price,
            if product.is_on_sale { format!("🏷️ PROMOÇÃO! De R${:.2}", product.original_price.unwrap_or(product.price * 1.5)) } else { String::new() },
            product.seller_name.as_deref().unwrap_or("Loja Oficial"),
            product.seller_rating.unwrap_or(4.5),
            product.price
        ),
        _ => format!(
            "{}\n\nPreço: R${:.2}\nAvaliação: {:.1}/5\nVendas: {}\n\n{}",
            product.title,
            product.price,
            product.product_rating.unwrap_or(4.5),
            product.sales_count,
            product.product_url
        ),
    }
}

// Helper function to export to CSV
fn export_to_csv(products: &[Product]) -> Result<String, String> {
    let mut csv =
        String::from("id,title,price,original_price,category,sales_count,rating,product_url\n");

    for p in products {
        csv.push_str(&format!(
            "{},{},{},{},{},{},{},{}\n",
            p.id,
            p.title.replace(',', ";"),
            p.price,
            p.original_price.unwrap_or(0.0),
            p.category.as_deref().unwrap_or(""),
            p.sales_count,
            p.product_rating.unwrap_or(0.0),
            p.product_url
        ));
    }

    Ok(csv)
}

// ==================================================
// SUBSCRIPTION COMMANDS (SaaS Híbrido)
// ==================================================

/// Validate subscription with API and cache locally for offline use
#[command]
pub async fn validate_subscription(
    app: AppHandle,
    auth_token: Option<String>,
) -> Result<SubscriptionValidation, String> {
    log::info!("Validating subscription...");

    let hwid = get_hardware_id();
    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");
    let cache_path = app_dir.join("subscription_cache.json");

    let client = reqwest::Client::new();
    
    // Build request with auth token if available
    let mut request = client.post(format!("{}/subscription/validate", API_URL));
    
    if let Some(token) = auth_token {
        request = request.header("Authorization", format!("Bearer {}", token));
    }

    let api_payload = json!({
        "hwid": hwid,
        "app_version": env!("CARGO_PKG_VERSION"),
    });

    match request.json(&api_payload).send().await {
        Ok(response) => {
            if response.status().is_success() {
                let api_response: serde_json::Value = response
                    .json()
                    .await
                    .map_err(|e| format!("Failed to parse API response: {}", e))?;

                // Parse subscription from API response
                let subscription = parse_subscription_from_api(&api_response)?;
                
                // Cache subscription for offline use
                let cached = CachedSubscription {
                    subscription: subscription.clone(),
                    cached_at: Utc::now().to_rfc3339(),
                    valid_until: calculate_cache_validity(&subscription),
                    last_sync: Utc::now().to_rfc3339(),
                };
                
                // Save to file
                if let Ok(json) = serde_json::to_string_pretty(&cached) {
                    let _ = fs::write(&cache_path, json);
                }
                
                // Also update database
                let _ = database::save_subscription_cache(&db_path, &cached);

                Ok(SubscriptionValidation {
                    is_valid: true,
                    subscription: Some(subscription),
                    reason: None,
                    message: Some("Subscription validated successfully".to_string()),
                })
            } else if response.status() == reqwest::StatusCode::UNAUTHORIZED {
                // Invalid token - clear cache and return invalid
                let _ = fs::remove_file(&cache_path);
                
                Ok(SubscriptionValidation {
                    is_valid: false,
                    subscription: None,
                    reason: Some("unauthorized".to_string()),
                    message: Some("Authentication required".to_string()),
                })
            } else if response.status() == reqwest::StatusCode::PAYMENT_REQUIRED {
                // Subscription expired or payment issue
                Ok(SubscriptionValidation {
                    is_valid: false,
                    subscription: None,
                    reason: Some("payment_required".to_string()),
                    message: Some("Subscription payment required".to_string()),
                })
            } else {
                log::warn!("Subscription API error: {}", response.status());
                // Try cached subscription
                try_cached_subscription(&cache_path, &db_path)
            }
        }
        Err(e) => {
            log::warn!("Subscription API connection failed: {}", e);
            // Offline mode - try cached subscription
            try_cached_subscription(&cache_path, &db_path)
        }
    }
}

/// Get cached subscription (for offline mode)
#[command]
pub async fn get_cached_subscription(app: AppHandle) -> Result<Option<CachedSubscription>, String> {
    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let cache_path = app_dir.join("subscription_cache.json");
    
    if cache_path.exists() {
        let content = fs::read_to_string(&cache_path)
            .map_err(|e| format!("Failed to read cache: {}", e))?;
        let cached: CachedSubscription = serde_json::from_str(&content)
            .map_err(|e| format!("Failed to parse cache: {}", e))?;
        
        // Check if cache is still valid
        if is_cache_valid(&cached) {
            return Ok(Some(cached));
        }
    }
    
    Ok(None)
}

/// Check if user can use a specific feature
#[command]
pub async fn check_feature_access(
    app: AppHandle,
    feature: String,
) -> Result<FeatureAccessResult, String> {
    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let cache_path = app_dir.join("subscription_cache.json");
    
    // Load cached subscription
    let cached = if cache_path.exists() {
        let content = fs::read_to_string(&cache_path)
            .map_err(|e| format!("Failed to read cache: {}", e))?;
        serde_json::from_str::<CachedSubscription>(&content).ok()
    } else {
        None
    };
    
    match cached {
        Some(c) if is_cache_valid(&c) => {
            let has_access = check_subscription_feature(&c.subscription, &feature);
            let limit = get_feature_limit(&c.subscription, &feature);
            
            Ok(FeatureAccessResult {
                feature,
                has_access,
                limit,
                current_usage: 0, // Would need to track locally
                plan_required: get_required_plan_for_feature(&feature),
            })
        }
        _ => {
            // No valid subscription - FREE plan features only
            let has_access = is_free_feature(&feature);
            Ok(FeatureAccessResult {
                feature,
                has_access,
                limit: get_free_limit(&feature),
                current_usage: 0,
                plan_required: if has_access { None } else { Some("starter".to_string()) },
            })
        }
    }
}

/// Get current execution mode
#[command]
pub async fn get_execution_mode(app: AppHandle) -> Result<ExecutionMode, String> {
    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let cache_path = app_dir.join("subscription_cache.json");
    
    if cache_path.exists() {
        let content = fs::read_to_string(&cache_path)
            .map_err(|e| format!("Failed to read cache: {}", e))?;
        if let Ok(cached) = serde_json::from_str::<CachedSubscription>(&content) {
            if is_cache_valid(&cached) {
                return Ok(cached.subscription.execution_mode);
            }
        }
    }
    
    // Default to web_only for free/unknown
    Ok(ExecutionMode::WebOnly)
}

/// Check if offline mode is allowed
#[command]
pub async fn can_work_offline(app: AppHandle) -> Result<OfflineStatus, String> {
    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let cache_path = app_dir.join("subscription_cache.json");
    
    if !cache_path.exists() {
        return Ok(OfflineStatus {
            allowed: false,
            days_remaining: 0,
            reason: Some("No cached subscription".to_string()),
        });
    }
    
    let content = fs::read_to_string(&cache_path)
        .map_err(|e| format!("Failed to read cache: {}", e))?;
    let cached: CachedSubscription = serde_json::from_str(&content)
        .map_err(|e| format!("Failed to parse cache: {}", e))?;
    
    // Check if subscription allows offline mode
    if !cached.subscription.features.offline_mode {
        return Ok(OfflineStatus {
            allowed: false,
            days_remaining: 0,
            reason: Some("Plan does not support offline mode".to_string()),
        });
    }
    
    // Check how many offline days remaining
    let cached_at = chrono::DateTime::parse_from_rfc3339(&cached.cached_at)
        .map_err(|e| format!("Invalid cached_at: {}", e))?;
    let days_offline = (Utc::now().signed_duration_since(cached_at.with_timezone(&Utc))).num_days();
    let days_remaining = cached.subscription.offline_days_allowed as i64 - days_offline;
    
    if days_remaining <= 0 {
        return Ok(OfflineStatus {
            allowed: false,
            days_remaining: 0,
            reason: Some("Offline period expired. Please connect to sync.".to_string()),
        });
    }
    
    Ok(OfflineStatus {
        allowed: true,
        days_remaining: days_remaining as i32,
        reason: None,
    })
}

// ==================================================
// SUBSCRIPTION HELPER TYPES
// ==================================================

#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct FeatureAccessResult {
    pub feature: String,
    pub has_access: bool,
    pub limit: Option<i32>,
    pub current_usage: i32,
    pub plan_required: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct OfflineStatus {
    pub allowed: bool,
    pub days_remaining: i32,
    pub reason: Option<String>,
}

// ==================================================
// SUBSCRIPTION HELPER FUNCTIONS
// ==================================================

fn parse_subscription_from_api(response: &serde_json::Value) -> Result<Subscription, String> {
    let plan_tier = match response["planTier"].as_str().unwrap_or("free") {
        "starter" => PlanTier::Starter,
        "business" => PlanTier::Business,
        "enterprise" => PlanTier::Enterprise,
        _ => PlanTier::Free,
    };
    
    let execution_mode = match response["executionMode"].as_str().unwrap_or("web_only") {
        "hybrid" => ExecutionMode::Hybrid,
        "local_first" => ExecutionMode::LocalFirst,
        _ => ExecutionMode::WebOnly,
    };
    
    let status = match response["status"].as_str().unwrap_or("active") {
        "trialing" => SubscriptionStatus::Trialing,
        "past_due" => SubscriptionStatus::PastDue,
        "canceled" => SubscriptionStatus::Canceled,
        "expired" => SubscriptionStatus::Expired,
        _ => SubscriptionStatus::Active,
    };
    
    // Parse marketplaces
    let marketplaces: Vec<MarketplaceAccess> = response["marketplaces"]
        .as_array()
        .map(|arr| {
            arr.iter().filter_map(|v| {
                match v.as_str()? {
                    "tiktok" => Some(MarketplaceAccess::Tiktok),
                    "aliexpress" => Some(MarketplaceAccess::Aliexpress),
                    "shopee" => Some(MarketplaceAccess::Shopee),
                    "amazon" => Some(MarketplaceAccess::Amazon),
                    "mercadolivre" => Some(MarketplaceAccess::Mercadolivre),
                    _ => None,
                }
            }).collect()
        })
        .unwrap_or_else(|| vec![MarketplaceAccess::Tiktok]);
    
    // Parse limits
    let limits_obj = &response["limits"];
    let limits = SubscriptionLimits {
        price_searches: limits_obj["price_searches"].as_i64().unwrap_or(50) as i32,
        favorites: limits_obj["favorites"].as_i64().unwrap_or(20) as i32,
        whatsapp_messages: limits_obj["whatsapp_messages"].as_i64().unwrap_or(0) as i32,
        api_calls: limits_obj["api_calls"].as_i64().unwrap_or(0) as i32,
        crm_leads: limits_obj["crm_leads"].as_i64().unwrap_or(0) as i32,
        chatbot_flows: limits_obj["chatbot_flows"].as_i64().unwrap_or(0) as i32,
        social_posts: limits_obj["social_posts"].as_i64().unwrap_or(0) as i32,
    };
    
    // Parse features
    let features_obj = &response["features"];
    let features = SubscriptionFeatures {
        chatbot_ai: features_obj["chatbot_ai"].as_bool().unwrap_or(false),
        analytics_advanced: features_obj["analytics_advanced"].as_bool().unwrap_or(false),
        analytics_export: features_obj["analytics_export"].as_bool().unwrap_or(false),
        crm_automation: features_obj["crm_automation"].as_bool().unwrap_or(false),
        api_access: features_obj["api_access"].as_bool().unwrap_or(false),
        offline_mode: features_obj["offline_mode"].as_bool().unwrap_or(false),
        hybrid_sync: features_obj["hybrid_sync"].as_bool().unwrap_or(false),
        priority_support: features_obj["priority_support"].as_bool().unwrap_or(false),
    };
    
    Ok(Subscription {
        id: response["id"].as_str().unwrap_or("").to_string(),
        user_id: response["userId"].as_str().unwrap_or("").to_string(),
        plan_tier,
        status,
        execution_mode,
        billing_cycle: response["billingCycle"].as_str().unwrap_or("monthly").to_string(),
        current_period_start: response["currentPeriodStart"].as_str().unwrap_or("").to_string(),
        current_period_end: response["currentPeriodEnd"].as_str().unwrap_or("").to_string(),
        marketplaces,
        limits,
        features,
        cached_at: Utc::now().to_rfc3339(),
        offline_days_allowed: response["offlineDays"].as_i64().unwrap_or(0) as i32,
        grace_period_days: response["gracePeriodDays"].as_i64().unwrap_or(3) as i32,
    })
}

fn calculate_cache_validity(subscription: &Subscription) -> String {
    let days = match subscription.plan_tier {
        PlanTier::Enterprise => 30,
        PlanTier::Business => 14,
        PlanTier::Starter => 7,
        PlanTier::Free => 1,
    };
    
    Utc::now()
        .checked_add_signed(chrono::Duration::days(days))
        .unwrap_or_else(Utc::now)
        .to_rfc3339()
}

fn is_cache_valid(cached: &CachedSubscription) -> bool {
    if let Ok(valid_until) = chrono::DateTime::parse_from_rfc3339(&cached.valid_until) {
        return Utc::now() < valid_until.with_timezone(&Utc);
    }
    false
}

fn try_cached_subscription(
    cache_path: &std::path::Path,
    db_path: &std::path::Path,
) -> Result<SubscriptionValidation, String> {
    // Try file cache first
    if cache_path.exists() {
        if let Ok(content) = fs::read_to_string(cache_path) {
            if let Ok(cached) = serde_json::from_str::<CachedSubscription>(&content) {
                if is_cache_valid(&cached) {
                    return Ok(SubscriptionValidation {
                        is_valid: true,
                        subscription: Some(cached.subscription),
                        reason: Some("offline_cached".to_string()),
                        message: Some("Using cached subscription (offline mode)".to_string()),
                    });
                }
            }
        }
    }
    
    // Try database cache
    if let Ok(Some(cached)) = database::get_subscription_cache(db_path) {
        if is_cache_valid(&cached) {
            return Ok(SubscriptionValidation {
                is_valid: true,
                subscription: Some(cached.subscription),
                reason: Some("offline_db_cached".to_string()),
                message: Some("Using database cached subscription".to_string()),
            });
        }
    }
    
    // No valid cache - return free tier fallback
    Ok(SubscriptionValidation {
        is_valid: true,
        subscription: Some(create_free_subscription()),
        reason: Some("offline_free_fallback".to_string()),
        message: Some("Offline - using free tier. Connect to sync subscription.".to_string()),
    })
}

fn create_free_subscription() -> Subscription {
    Subscription {
        id: "free".to_string(),
        user_id: "offline".to_string(),
        plan_tier: PlanTier::Free,
        status: SubscriptionStatus::Active,
        execution_mode: ExecutionMode::WebOnly,
        billing_cycle: "none".to_string(),
        current_period_start: Utc::now().to_rfc3339(),
        current_period_end: Utc::now()
            .checked_add_signed(chrono::Duration::days(365))
            .unwrap()
            .to_rfc3339(),
        marketplaces: vec![MarketplaceAccess::Tiktok],
        limits: SubscriptionLimits {
            price_searches: 50,
            favorites: 20,
            whatsapp_messages: 0,
            api_calls: 0,
            crm_leads: 0,
            chatbot_flows: 0,
            social_posts: 0,
        },
        features: SubscriptionFeatures::default(),
        cached_at: Utc::now().to_rfc3339(),
        offline_days_allowed: 0,
        grace_period_days: 3,
    }
}

fn check_subscription_feature(subscription: &Subscription, feature: &str) -> bool {
    match feature {
        "chatbot_ai" => subscription.features.chatbot_ai,
        "analytics_advanced" => subscription.features.analytics_advanced,
        "analytics_export" => subscription.features.analytics_export,
        "crm_automation" => subscription.features.crm_automation,
        "api_access" => subscription.features.api_access,
        "offline_mode" => subscription.features.offline_mode,
        "hybrid_sync" => subscription.features.hybrid_sync,
        "priority_support" => subscription.features.priority_support,
        // Metered features - check limits
        "price_searches" => subscription.limits.price_searches > 0,
        "favorites" => subscription.limits.favorites > 0,
        "whatsapp_messages" => subscription.limits.whatsapp_messages > 0,
        "api_calls" => subscription.limits.api_calls > 0,
        _ => false,
    }
}

fn get_feature_limit(subscription: &Subscription, feature: &str) -> Option<i32> {
    match feature {
        "price_searches" => Some(subscription.limits.price_searches),
        "favorites" => Some(subscription.limits.favorites),
        "whatsapp_messages" => Some(subscription.limits.whatsapp_messages),
        "api_calls" => Some(subscription.limits.api_calls),
        "crm_leads" => Some(subscription.limits.crm_leads),
        "chatbot_flows" => Some(subscription.limits.chatbot_flows),
        "social_posts" => Some(subscription.limits.social_posts),
        _ => None,
    }
}

fn get_required_plan_for_feature(feature: &str) -> Option<String> {
    match feature {
        "chatbot_ai" | "crm_automation" | "api_access" => Some("business".to_string()),
        "analytics_advanced" | "analytics_export" | "offline_mode" | "hybrid_sync" => {
            Some("starter".to_string())
        }
        "priority_support" => Some("enterprise".to_string()),
        _ => None,
    }
}

fn is_free_feature(feature: &str) -> bool {
    matches!(feature, "price_searches" | "favorites" | "analytics_basic")
}

fn get_free_limit(feature: &str) -> Option<i32> {
    match feature {
        "price_searches" => Some(50),
        "favorites" => Some(20),
        _ => Some(0),
    }
}
