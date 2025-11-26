// Scraper Module - Main Entry Point
// Coordinates all scraping submodules

pub mod antibot;
pub mod browser;
pub mod models;
pub mod parser;
pub mod pool;
pub mod proxy;
pub mod research_api;

pub use antibot::AntiDetection;
pub use browser::BrowserManager;
pub use parser::TikTokParser;
pub use proxy::ProxyPool;
pub use research_api::ResearchApi;

use crate::models::{Product, ScraperStatus};
use anyhow::{Context, Result};
use rand::Rng;
use std::sync::Arc;
use sysinfo::System;
// Ensure SystemExt is available if needed, or just System
use tokio::sync::Mutex;

use self::models::ScraperConfig;

/// Main TikTok Scraper
pub struct TikTokScraper {
    browser: BrowserManager,
    parser: TikTokParser,
    antibot: AntiDetection,
    proxy_pool: Option<ProxyPool>,
    status: Arc<Mutex<ScraperStatus>>,
    config: ScraperConfig,
    system: Arc<Mutex<System>>,
    research_api: ResearchApi,
}

impl TikTokScraper {
    pub fn new(config: ScraperConfig, status: Arc<Mutex<ScraperStatus>>) -> Self {
        let proxy_pool = if config.use_proxy && !config.proxies.is_empty() {
            Some(ProxyPool::new(config.proxies.clone()))
        } else {
            None
        };

        let mut browser =
            BrowserManager::new(config.headless).with_timeout(config.page_load_timeout_ms / 1000);

        if let Some(path) = &config.user_data_path {
            browser = browser.with_user_data(std::path::PathBuf::from(path));
        }

        let research_api = ResearchApi::new(config.api_key.clone(), config.api_secret.clone());

        Self {
            browser,
            parser: TikTokParser::new(config.selectors.clone()),
            antibot: AntiDetection::new(),
            proxy_pool,
            status,
            config,
            system: Arc::new(Mutex::new(System::new_all())),
            research_api,
        }
    }

    async fn add_log(&self, message: String) {
        let mut status = self.status.lock().await;
        let timestamp = chrono::Local::now().format("%H:%M:%S").to_string();
        let log_entry = format!("[{}] {}", timestamp, message);

        status.logs.push(log_entry);

        // Keep only last 50 logs
        if status.logs.len() > 50 {
            status.logs.remove(0);
        }
    }

    pub async fn start(&self) -> Result<Vec<Product>> {
        log::info!("Iniciando scraper do TikTok Shop...");
        self.add_log("🚀 Iniciando scraper do TikTok Shop...".to_string())
            .await;

        // Safety Switch Check
        if self.config.safety_switch_enabled {
            // In a real implementation, we would check persistent state here.
            // For now, we just log that it's enabled.
            self.add_log("🛡️ Safety Switch: ATIVADO".to_string()).await;
        }

        let mut status = self.status.lock().await;
        status.is_running = true;
        status.progress = 0.0;
        status.started_at = Some(chrono::Utc::now().to_rfc3339());
        status.status_message = Some("Inicializando...".to_string());
        drop(status);

        let result = self.scrape_products().await;

        let mut status = self.status.lock().await;
        status.is_running = false;
        status.progress = 100.0;
        status.status_message = Some("Finalizado".to_string());

        match &result {
            Ok(products) => {
                status.products_found = products.len() as i32;
                log::info!(
                    "Scraping concluído: {} produtos encontrados",
                    products.len()
                );
                // Log added inside scrape_products
            }
            Err(e) => {
                status.errors.push(format!("Falha no scraping: {}", e));
                log::error!("Falha no scraping: {}", e);
                // Log added inside scrape_products or here
            }
        }

        self.add_log("🏁 Processo finalizado.".to_string()).await;
        result
    }

    async fn scrape_products(&self) -> Result<Vec<Product>> {
        // Get proxy if enabled
        let proxy = if self.config.use_proxy {
            if let Some(pool) = &self.proxy_pool {
                pool.get_next().await.map(|p| p.to_url())
            } else {
                None
            }
        } else {
            None
        };

        {
            let mut status = self.status.lock().await;
            status.status_message = Some("Iniciando navegador...".to_string());
        }

        // Start browser
        self.browser
            .start(proxy)
            .await
            .context("Failed to start browser")?;

        {
            let mut status = self.status.lock().await;
            status.status_message = Some("Navegador iniciado".to_string());
        }

        // Create new page
        let page = self
            .browser
            .new_page()
            .await
            .context("Failed to create page")?;

        // Generate fingerprint
        let fingerprint = self.antibot.generate_fingerprint();

        // Inject anti-detection scripts
        self.antibot
            .inject_stealth_scripts(&page, Some(&fingerprint))
            .await
            .context("Failed to inject stealth scripts")?;

        let mut all_products = Vec::new();
        let categories = if self.config.categories.is_empty() {
            vec!["trending".to_string()]
        } else {
            self.config.categories.clone()
        };

        for category in categories {
            // Check if stopped
            if !self.status.lock().await.is_running {
                self.add_log("🛑 Scraper parado pelo usuário.".to_string())
                    .await;
                break;
            }

            if all_products.len() >= self.config.max_products as usize {
                break;
            }

            let url = if category == "trending" {
                "https://shop.tiktok.com/browse".to_string()
            } else if category.starts_with("http") || category.starts_with("file") {
                category.clone()
            } else {
                format!("https://shop.tiktok.com/search?keyword={}", category)
            };

            log::info!("Navigating to: {}", url);
            self.add_log(format!("🌐 Navegando para: {}", category))
                .await;

            // Resource Check
            {
                let mut sys = self.system.lock().await;
                sys.refresh_memory();
                let used_mem = sys.used_memory();
                let total_mem = sys.total_memory();
                if total_mem > 0 && (used_mem as f64 / total_mem as f64) > 0.9 {
                    self.add_log("⚠️ Memória cheia! Pausando por 10s...".to_string())
                        .await;
                    tokio::time::sleep(tokio::time::Duration::from_secs(10)).await;
                }
            }

            // Exponential Backoff
            let mut retries = 0;
            let max_retries = self.config.max_retries;
            loop {
                // Check if stopped
                if !self.status.lock().await.is_running {
                    self.add_log("🛑 Scraper parado pelo usuário.".to_string())
                        .await;
                    break;
                }

                match page.goto(&url).await {
                    Ok(_) => break,
                    Err(e) => {
                        retries += 1;
                        if retries > max_retries {
                            return Err(anyhow::anyhow!("Failed to navigate: {}", e));
                        }

                        // Check if stopped before waiting
                        if !self.status.lock().await.is_running {
                            self.add_log("🛑 Scraper parado pelo usuário.".to_string())
                                .await;
                            break;
                        }

                        let delay = 2u64.pow(retries as u32);
                        self.add_log(format!(
                            "⚠️ Erro ao carregar. Tentando novamente em {}s...",
                            delay
                        ))
                        .await;
                        tokio::time::sleep(tokio::time::Duration::from_secs(delay)).await;
                    }
                }
            }

            // Check if stopped after navigation loop
            if !self.status.lock().await.is_running {
                break;
            }

            // Wait for page to load
            self.add_log("⏳ Aguardando carregamento da página...".to_string())
                .await;

            // Rate Limiting: 5-10 seconds (Aggressive mitigation)
            let delay = rand::thread_rng().gen_range(5000..=10000);

            // Check if stopped before waiting
            if !self.status.lock().await.is_running {
                break;
            }

            tokio::time::sleep(tokio::time::Duration::from_millis(delay)).await;

            // Check if stopped after waiting
            if !self.status.lock().await.is_running {
                break;
            }

            // Safety Switch: Check for immediate blocks/captchas
            let content = page.content().await.unwrap_or_default();
            if content.contains("captcha")
                || content.contains("verify")
                || content.contains("Access Denied")
            {
                self.add_log(
                    "⚠️ DETECÇÃO DE BOT IDENTIFICADA! Abortando para segurança.".to_string(),
                )
                .await;

                if let Some(db_path) = &self.config.db_path {
                    let _ = crate::database::save_error_page(
                        std::path::Path::new(db_path),
                        &url,
                        &content,
                    );
                }

                if self.config.safety_switch_enabled {
                    return Err(anyhow::anyhow!("Safety Switch triggered: Bot detection"));
                }
            }

            // Simulate human interaction
            if self.status.lock().await.is_running {
                self.browser.simulate_human_interaction(&page).await.ok();
            }

            // Scroll and load more
            let mut previous_height = 0;
            let mut no_change_count = 0;

            while all_products.len() < self.config.max_products as usize {
                // Check if stopped
                if !self.status.lock().await.is_running {
                    break;
                }

                // Parse current products
                self.add_log("🔍 Analisando produtos na página...".to_string())
                    .await;
                let products = self.parser.parse_product_list(&page).await?;

                // Add new products (deduplicate by ID)
                let mut new_count = 0;
                for p in products {
                    if !all_products
                        .iter()
                        .any(|existing: &Product| existing.tiktok_id == p.tiktok_id)
                    {
                        self.add_log(format!(
                            "✨ Encontrado: {} (R$ {:.2})",
                            p.title.chars().take(30).collect::<String>(),
                            p.price
                        ))
                        .await;
                        all_products.push(p);
                        new_count += 1;
                    }
                }

                if new_count > 0 {
                    self.add_log(format!("📦 +{} novos produtos adicionados", new_count))
                        .await;
                }

                // Update progress
                let mut status = self.status.lock().await;
                status.products_found = all_products.len() as i32;
                status.progress =
                    (all_products.len() as f32 / self.config.max_products as f32 * 100.0).min(99.0);
                drop(status);

                if all_products.len() >= self.config.max_products as usize {
                    break;
                }

                // Scroll down
                self.add_log("⬇️ Rolando página para carregar mais...".to_string())
                    .await;
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    .await?;

                // Check if stopped
                if !self.status.lock().await.is_running {
                    break;
                }

                tokio::time::sleep(tokio::time::Duration::from_millis(2000)).await;

                // Check if we reached bottom
                let height_val = page
                    .evaluate("document.body.scrollHeight")
                    .await?
                    .into_value::<i64>();
                let current_height = match height_val {
                    Ok(h) => h,
                    Err(_) => previous_height, // Keep same if failed to parse
                };

                if current_height == previous_height {
                    no_change_count += 1;
                    if no_change_count >= 3 {
                        self.add_log("⚠️ Fim da página alcançado.".to_string()).await;
                        break; // Stop if no new content after 3 scrolls
                    }
                } else {
                    no_change_count = 0;
                }
                previous_height = current_height;
            }
        }

        log::info!("Parsed {} products total", all_products.len());

        // Cleanup
        self.browser.stop().await?;

        Ok(all_products)
    }

    #[allow(dead_code)]
    pub async fn get_status(&self) -> ScraperStatus {
        self.status.lock().await.clone()
    }

    #[allow(dead_code)]
    pub async fn stop(&self) {
        let mut status = self.status.lock().await;
        status.is_running = false;
        drop(status);

        if let Err(e) = self.browser.stop().await {
            log::error!("Error stopping browser: {}", e);
        }
    }
}

impl Default for TikTokScraper {
    fn default() -> Self {
        Self::new(
            ScraperConfig::default(),
            Arc::new(Mutex::new(ScraperStatus {
                is_running: false,
                progress: 0.0,
                current_product: None,
                products_found: 0,
                errors: vec![],
                logs: vec![],
                started_at: None,
                status_message: None,
            })),
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::scraper::models::ScraperConfig;

    #[tokio::test]
    async fn test_e2e_scraping() {
        // Initialize logger for test output
        let _ = env_logger::builder().is_test(true).try_init();

        // Resolve fixture path
        let mut fixture_path = std::env::current_dir().unwrap();
        fixture_path.push("tests");
        fixture_path.push("fixtures");
        fixture_path.push("tiktok_shop.html");
        let fixture_url = format!("file://{}", fixture_path.to_string_lossy());

        println!("Using fixture URL: {}", fixture_url);

        // Setup configuration for test
        let config = ScraperConfig {
            headless: true,                // Run headless for automated test
            categories: vec![fixture_url], // Use fixture URL
            max_products: 5,
            ..ScraperConfig::default()
        };

        // Initialize scraper
        let scraper = TikTokScraper::new(
            config,
            Arc::new(Mutex::new(ScraperStatus {
                is_running: false,
                progress: 0.0,
                current_product: None,
                products_found: 0,
                errors: vec![],
                logs: vec![],
                started_at: None,
                status_message: None,
            })),
        );

        // Run scraper
        println!("Starting E2E scraper test...");
        let result = scraper.start().await;

        // Assertions
        match result {
            Ok(products) => {
                println!(
                    "Scraper finished successfully. Found {} products.",
                    products.len()
                );

                // Verify we found products
                assert!(!products.is_empty(), "Should find at least one product");

                // Verify product structure
                let first_product = &products[0];
                println!("First product: {:?}", first_product);

                assert!(
                    !first_product.title.is_empty(),
                    "Product title should not be empty"
                );
                assert!(
                    !first_product.tiktok_id.is_empty(),
                    "Product ID should not be empty"
                );
                assert!(
                    first_product.price > 0.0,
                    "Product price should be greater than 0"
                );
            }
            Err(e) => {
                panic!("Scraper failed: {}", e);
            }
        }
    }
}
