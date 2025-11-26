// Tauri commands - API for frontend
use crate::database;
use crate::models::*;
use crate::config::{AppSettings, ScraperConfig};
use std::fs;
use crate::scraper::TikTokScraper;
use crate::ScraperState;
use chrono::Utc;
use tauri::{command, AppHandle, Manager, State};
use sysinfo::{System, Networks};
use sha2::{Sha256, Digest};
use serde_json::json;

const API_URL: &str = "http://localhost:8000";

fn get_hardware_id() -> String {
    let mut sys = System::new_all();
    sys.refresh_all();
    
    let cpu_id = sys.cpus().iter()
        .map(|cpu| cpu.brand())
        .collect::<Vec<_>>()
        .join("");
        
    let networks = Networks::new_with_refreshed_list();
    let mac_addresses = networks.iter()
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
    
    database::search_products(&db_path, &filters)
        .map_err(|e| format!("Database error: {}", e))
}

/// Get single product by ID
#[command]
pub async fn get_product_by_id(
    app: AppHandle,
    id: String,
) -> Result<Option<Product>, String> {
    log::info!("Getting product by id: {}", id);
    
    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");
    
    database::get_product_by_id(&db_path, &id)
        .map_err(|e| format!("Database error: {}", e))
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
    
    database::add_favorite(&db_path, &user_id, &product_id, list_id.as_deref(), notes.as_deref())
        .map_err(|e| format!("Database error: {}", e))
}

/// Remove product from favorites
#[command]
pub async fn remove_favorite(
    app: AppHandle,
    product_id: String,
) -> Result<bool, String> {
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
    
    database::create_favorite_list(&db_path, &user_id, &name, description.as_deref(), color.as_deref(), icon.as_deref())
        .map_err(|e| format!("Database error: {}", e))
}

/// Get all favorite lists
#[command]
pub async fn get_favorite_lists(
    app: AppHandle,
) -> Result<Vec<FavoriteList>, String> {
    log::info!("Getting favorite lists");
    
    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");
    
    let user_id = "default_user".to_string();
    
    database::get_favorite_lists(&db_path, &user_id)
        .map_err(|e| format!("Database error: {}", e))
}

/// Delete favorite list
#[command]
pub async fn delete_favorite_list(
    app: AppHandle,
    list_id: String,
) -> Result<bool, String> {
    log::info!("Deleting favorite list: {}", list_id);
    
    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");
    
    database::delete_favorite_list(&db_path, &list_id)
        .map_err(|e| format!("Database error: {}", e))
}

/// Generate AI copy for product
#[command]
pub async fn generate_copy(
    app: AppHandle,
    request: CopyRequest,
) -> Result<CopyResponse, String> {
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

    let copy_content = match client.post(format!("{}/copy/generate", API_URL))
        .json(&api_payload)
        .send()
        .await 
    {
        Ok(response) => {
            if response.status().is_success() {
                let api_response: serde_json::Value = response.json().await
                    .map_err(|e| format!("Failed to parse API response: {}", e))?;
                
                api_response["copy_text"].as_str()
                    .unwrap_or_else(|| "Error: Empty response from AI")
                    .to_string()
            } else {
                log::warn!("API error: {}, falling back to local template", response.status());
                generate_copy_content(&product, &request.copy_type, &request.tone)
            }
        },
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
    ).ok();
    
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
pub async fn get_user_stats(
    app: AppHandle,
) -> Result<DashboardStats, String> {
    log::info!("Getting user stats");
    
    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let db_path = app_dir.join("tiktrend.db");
    
    let user_id = "default_user".to_string();
    
    database::get_dashboard_stats(&db_path, &user_id)
        .map_err(|e| format!("Database error: {}", e))
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

    match client.post(format!("{}/license/validate", API_URL))
        .json(&api_payload)
        .send()
        .await 
    {
        Ok(response) => {
            if response.status().is_success() {
                let api_response: serde_json::Value = response.json().await
                    .map_err(|e| format!("Failed to parse API response: {}", e))?;

                let features = api_response["features"].as_object()
                    .ok_or("Invalid features format")?;

                Ok(License {
                    is_valid: api_response["valid"].as_bool().unwrap_or(false),
                    plan: api_response["plan"].as_str().unwrap_or("free").to_string(),
                    features: PlanFeatures {
                        searches_per_month: features.get("searches_per_month").and_then(|v| v.as_i64()).unwrap_or(0) as i32,
                        copies_per_month: features.get("copies_per_month").and_then(|v| v.as_i64()).unwrap_or(0) as i32,
                        favorite_lists: features.get("favorite_lists").and_then(|v| v.as_i64()).unwrap_or(0) as i32,
                        export_enabled: features.get("export_enabled").and_then(|v| v.as_bool()).unwrap_or(false),
                        scheduler_enabled: features.get("scheduler_enabled").and_then(|v| v.as_bool()).unwrap_or(false),
                    },
                    expires_at: api_response["expires_at"].as_str().unwrap_or("").to_string(),
                    usage_this_month: UsageStats {
                        searches: 0,
                        copies: 0,
                    },
                })
            } else {
                // Fallback to trial if API fails (e.g. 404, 500)
                // But if 403/401 it means invalid.
                // For development, let's fallback to trial if connection fails
                log::warn!("License API error: {}", response.status());
                Err(format!("License validation failed: {}", response.status()))
            }
        },
        Err(e) => {
            log::warn!("License API connection failed: {}", e);
            // Fallback to trial for offline dev
             Ok(License {
                is_valid: true,
                plan: String::from("trial (offline)"),
                features: PlanFeatures {
                    searches_per_month: 10,
                    copies_per_month: 5,
                    favorite_lists: 2,
                    export_enabled: false,
                    scheduler_enabled: false,
                },
                expires_at: chrono::Utc::now()
                    .checked_add_signed(chrono::Duration::days(7))
                    .unwrap()
                    .to_rfc3339(),
                usage_this_month: UsageStats {
                    searches: 0,
                    copies: 0,
                },
            })
        }
    }
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
    let db_path = app_dir.join("tiktrend.db");
    
    // Convert config to scraper config
    let scraper_config = crate::scraper::models::ScraperConfig::from(config);
    let scraper = TikTokScraper::new(scraper_config);
    let products = scraper.start().await
        .map_err(|e| e.to_string())?;
    
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
pub async fn get_scraper_status(
    state: State<'_, ScraperState>,
) -> Result<ScraperStatus, String> {
    let status = state.0.lock().await;
    Ok(status.clone())
}

/// Stop running scraper
#[command]
pub async fn stop_scraper(
    state: State<'_, ScraperState>,
) -> Result<bool, String> {
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
pub async fn save_settings(
    app: AppHandle,
    settings: AppSettings,
) -> Result<(), String> {
    let app_dir = app.path().app_data_dir().map_err(|e| e.to_string())?;
    let config_path = app_dir.join("settings.json");
    
    let content = serde_json::to_string_pretty(&settings).map_err(|e| e.to_string())?;
    fs::write(config_path, content).map_err(|e| e.to_string())?;
    
    Ok(())
}

/// Get app settings
#[command]
pub async fn get_settings(
    app: AppHandle,
) -> Result<AppSettings, String> {
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
    log::info!("Exporting {} products to {} as {}", product_ids.len(), path, format);
    
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
            if product.in_stock { "Disponível" } else { "Indisponível" }
        ),
        "whatsapp" => format!(
            "Oi! 👋\n\nVi esse produto incrível e lembrei de você:\n\n*{}*\n\n💰 R${:.2}\n⭐ Nota {:.1}\n{} {} vendidos\n{}\n\nO que achou? 😊",
            product.title,
            product.price,
            product.product_rating.unwrap_or(4.5),
            emoji_cart,
            product.sales_count,
            if product.has_free_shipping { "🚚 Frete grátis!" } else { "" }
        ),
        "story_reels" => format!(
            "{} ACHADO DO DIA!\n\n{}\n\n{:.1}⭐ | {} vendidos\nR${:.2}\n\n📲 Link nos destaques!",
            emoji_fire,
            product.title,
            product.product_rating.unwrap_or(4.5),
            product.sales_count,
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
    let mut csv = String::from("id,title,price,original_price,category,sales_count,rating,product_url\n");
    
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
