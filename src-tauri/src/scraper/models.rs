// Scraper Data Models
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone)]
pub struct ScraperConfig {
    pub headless: bool,
    pub max_concurrent_browsers: usize,
    pub request_timeout_ms: u64,
    pub page_load_timeout_ms: u64,
    pub min_delay_ms: u64,
    pub max_delay_ms: u64,
    pub max_retries: usize,
    pub use_proxy: bool,
    pub proxies: Vec<String>,
    pub categories: Vec<String>,
    pub max_products: u32,
}

impl Default for ScraperConfig {
    fn default() -> Self {
        Self {
            headless: true,
            max_concurrent_browsers: 1,
            request_timeout_ms: 30000,
            page_load_timeout_ms: 60000,
            min_delay_ms: 2000,
            max_delay_ms: 5000,
            max_retries: 3,
            use_proxy: false,
            proxies: vec![],
            categories: vec![],
            max_products: 100,
        }
    }
}

// Convert from crate::config::ScraperConfig to scraper::models::ScraperConfig
impl From<crate::config::ScraperConfig> for ScraperConfig {
    fn from(config: crate::config::ScraperConfig) -> Self {
        Self {
            headless: config.headless,
            max_concurrent_browsers: 1,
            request_timeout_ms: config.timeout as u64 * 1000,
            page_load_timeout_ms: 60000,
            min_delay_ms: 2000,
            max_delay_ms: 5000,
            max_retries: 3,
            use_proxy: config.use_proxy,
            proxies: config.proxies.unwrap_or_default(),
            categories: config.categories,
            max_products: config.max_products,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScraperStatus {
    pub is_running: bool,
    pub progress: f32,
    pub current_product: Option<String>,
    pub products_found: usize,
    pub errors: Vec<String>,
    pub started_at: Option<String>,
}

impl Default for ScraperStatus {
    fn default() -> Self {
        Self {
            is_running: false,
            progress: 0.0,
            current_product: None,
            products_found: 0,
            errors: Vec::new(),
            started_at: None,
        }
    }
}

#[derive(Debug, Clone)]
pub struct ProxyConfig {
    pub server: String,
    pub username: Option<String>,
    pub password: Option<String>,
}

impl ProxyConfig {
    pub fn to_url(&self) -> String {
        if let (Some(user), Some(pass)) = (&self.username, &self.password) {
            format!("{}:{}@{}", user, pass, self.server)
        } else {
            self.server.clone()
        }
    }
}
