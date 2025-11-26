// Scraper Module - Main Entry Point
// Coordinates all scraping submodules

pub mod browser;
pub mod parser;
pub mod antibot;
pub mod proxy;
pub mod models;

pub use browser::BrowserManager;
pub use parser::TikTokParser;
pub use antibot::AntiDetection;
pub use proxy::ProxyPool;
pub use models::*;

use crate::models::{Product, ScraperStatus};
use anyhow::{Result, Context};
use std::sync::Arc;
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
}

impl TikTokScraper {
    pub fn new(config: ScraperConfig) -> Self {
        let proxy_pool = if config.use_proxy && !config.proxies.is_empty() {
            Some(ProxyPool::new(config.proxies.clone()))
        } else {
            None
        };
        
        Self {
            browser: BrowserManager::new(config.headless),
            parser: TikTokParser::new(),
            antibot: AntiDetection::new(),
            proxy_pool,
            status: Arc::new(Mutex::new(ScraperStatus {
                is_running: false,
                progress: 0.0,
                current_product: None,
                products_found: 0,
                errors: vec![],
                started_at: None,
            })),
            config,
        }
    }

    pub async fn start(&self) -> Result<Vec<Product>> {
        log::info!("Starting TikTok Shop scraper...");
        
        let mut status = self.status.lock().await;
        status.is_running = true;
        status.progress = 0.0;
        status.started_at = Some(chrono::Utc::now().to_rfc3339());
        drop(status);

        let result = self.scrape_products().await;
        
        let mut status = self.status.lock().await;
        status.is_running = false;
        status.progress = 100.0;
        
        match &result {
            Ok(products) => {
                status.products_found = products.len() as i32;
                log::info!("Scraping completed: {} products found", products.len());
            }
            Err(e) => {
                status.errors.push(format!("Scraping failed: {}", e));
                log::error!("Scraping failed: {}", e);
            }
        }
        
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

        // Start browser
        self.browser.start(proxy).await
            .context("Failed to start browser")?;
        
        // Create new page
        let page = self.browser.new_page().await
            .context("Failed to create page")?;
        
        // Generate fingerprint
        let fingerprint = self.antibot.generate_fingerprint();

        // Inject anti-detection scripts
        self.antibot.inject_stealth_scripts(&page, Some(&fingerprint)).await
            .context("Failed to inject stealth scripts")?;
            
        let mut all_products = Vec::new();
        let categories = if self.config.categories.is_empty() {
            vec!["trending".to_string()]
        } else {
            self.config.categories.clone()
        };

        for category in categories {
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
            
            page.goto(&url).await
                .context("Failed to navigate to TikTok Shop")?;
            
            // Wait for page to load
            tokio::time::sleep(tokio::time::Duration::from_millis(5000)).await;
            
            // Scroll and load more
            let mut previous_height = 0;
            let mut no_change_count = 0;
            
            while all_products.len() < self.config.max_products as usize {
                // Parse current products
                let products = self.parser.parse_product_list(&page).await?;
                
                // Add new products (deduplicate by ID)
                for p in products {
                    if !all_products.iter().any(|existing: &Product| existing.tiktok_id == p.tiktok_id) {
                        all_products.push(p);
                    }
                }
                
                // Update progress
                let mut status = self.status.lock().await;
                status.products_found = all_products.len() as i32;
                status.progress = (all_products.len() as f32 / self.config.max_products as f32 * 100.0).min(99.0);
                drop(status);
                
                if all_products.len() >= self.config.max_products as usize {
                    break;
                }

                // Scroll down
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)").await?;
                tokio::time::sleep(tokio::time::Duration::from_millis(2000)).await;
                
                // Check if we reached bottom
                let height_val = page.evaluate("document.body.scrollHeight").await?.into_value::<i64>();
                let current_height = match height_val {
                    Ok(h) => h,
                    Err(_) => previous_height // Keep same if failed to parse
                };

                if current_height == previous_height {
                    no_change_count += 1;
                    if no_change_count >= 3 {
                        break; // Stop if no new content after 3 scrolls
                    }
                } else {
                    previous_height = current_height;
                    no_change_count = 0;
                }
            }
        }
        
        log::info!("Parsed {} products total", all_products.len());
        
        // Cleanup
        self.browser.stop().await?;
        
        Ok(all_products)
    }

    pub async fn get_status(&self) -> ScraperStatus {
        self.status.lock().await.clone()
    }

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
        Self::new(ScraperConfig::default())
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
            headless: true, // Run headless for automated test
            categories: vec![fixture_url], // Use fixture URL
            max_products: 5,
            ..ScraperConfig::default()
        };

        // Initialize scraper
        let scraper = TikTokScraper::new(config);

        // Run scraper
        println!("Starting E2E scraper test...");
        let result = scraper.start().await;

        // Assertions
        match result {
            Ok(products) => {
                println!("Scraper finished successfully. Found {} products.", products.len());
                
                // Verify we found products
                assert!(!products.is_empty(), "Should find at least one product");
                
                // Verify product structure
                let first_product = &products[0];
                println!("First product: {:?}", first_product);
                
                assert!(!first_product.title.is_empty(), "Product title should not be empty");
                assert!(!first_product.tiktok_id.is_empty(), "Product ID should not be empty");
                assert!(first_product.price > 0.0, "Product price should be greater than 0");
            }
            Err(e) => {
                panic!("Scraper failed: {}", e);
            }
        }
    }
}
