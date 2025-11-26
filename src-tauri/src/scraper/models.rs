// Scraper Data Models
use ts_rs::TS;
#[derive(Debug, Clone, TS)]
#[ts(export)]
#[allow(dead_code)]
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
    pub user_data_path: Option<String>,
    pub db_path: Option<String>,
    pub selectors: Option<Vec<String>>, // Added
    // Safety Switch
    pub safety_switch_enabled: bool,
    pub max_detection_rate: f32,
    pub safety_cooldown_seconds: u64,
    pub consecutive_failures_threshold: u32,
    // Research API
    pub api_key: Option<String>,
    pub api_secret: Option<String>,
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
            user_data_path: None,
            db_path: None,
            selectors: None,
            safety_switch_enabled: true,
            max_detection_rate: 0.2,
            safety_cooldown_seconds: 3600,
            consecutive_failures_threshold: 5,
            api_key: None,
            api_secret: None,
        }
    }
}

// Convert from crate::config::ScraperConfig to scraper::models::ScraperConfig
impl From<crate::config::ScraperConfig> for ScraperConfig {
    fn from(config: crate::config::ScraperConfig) -> Self {
        Self {
            headless: config.headless,
            // ... other fields ...
            // We can't easily map user_data_path from config::ScraperConfig if it doesn't exist there.
            // But we can set it later or add it to config::ScraperConfig.
            // For now, let's assume None and let commands.rs set it.
            user_data_path: None,
            db_path: None,
            selectors: None,
            max_concurrent_browsers: 1,
            request_timeout_ms: config.timeout as u64 * 1000,
            page_load_timeout_ms: 60000,
            min_delay_ms: 2000,
            max_delay_ms: 5000,
            max_retries: 3,
            use_proxy: config.use_proxy,
            proxies: config.proxies.unwrap_or_default(),
            categories: config.categories,
            max_products: config.max_products as u32,
            safety_switch_enabled: true,
            max_detection_rate: 0.2,
            safety_cooldown_seconds: 3600,
            consecutive_failures_threshold: 5,
            api_key: None,
            api_secret: None,
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
