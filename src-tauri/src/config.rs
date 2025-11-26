use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct CredentialsConfig {
    pub openai_key: String,
    pub proxies: Vec<String>,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct ScraperConfig {
    pub max_products: u32,
    pub interval_minutes: u32,
    pub categories: Vec<String>,
    pub use_proxy: bool,
    pub proxies: Option<Vec<String>>,
    pub headless: bool,
    pub timeout: u32,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct LicenseConfig {
    pub key: Option<String>,
    pub plan: String,
    pub expires_at: Option<String>,
    pub trial_started: Option<String>,
    pub is_active: bool,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct SystemConfig {
    pub auto_update: bool,
    pub check_interval: u32,
    pub logs_enabled: bool,
    pub max_log_size: u32,
    pub analytics_enabled: bool,
}

#[derive(Debug, Serialize, Deserialize, Clone)]
#[serde(rename_all = "camelCase")]
pub struct AppSettings {
    pub theme: String,
    pub language: String,
    pub notifications_enabled: bool,
    pub auto_update: bool,
    pub max_products_per_search: u32,
    pub cache_images: bool,
    pub proxy_enabled: bool,
    pub proxy_list: Vec<String>,
    pub openai_model: String,
    pub default_copy_type: String,
    pub default_copy_tone: String,
    
    pub credentials: CredentialsConfig,
    pub scraper: ScraperConfig,
    pub license: LicenseConfig,
    pub system: SystemConfig,
}

impl Default for AppSettings {
    fn default() -> Self {
        Self {
            theme: "system".to_string(),
            language: "pt-BR".to_string(),
            notifications_enabled: true,
            auto_update: true,
            max_products_per_search: 50,
            cache_images: true,
            proxy_enabled: false,
            proxy_list: Vec::new(),
            openai_model: "gpt-4".to_string(),
            default_copy_type: "tiktok_hook".to_string(),
            default_copy_tone: "urgent".to_string(),
            
            credentials: CredentialsConfig {
                openai_key: "".to_string(),
                proxies: Vec::new(),
            },
            scraper: ScraperConfig {
                max_products: 50,
                interval_minutes: 60,
                categories: Vec::new(),
                use_proxy: false,
                proxies: None,
                headless: true,
                timeout: 30000,
            },
            license: LicenseConfig {
                key: None,
                plan: "trial".to_string(),
                expires_at: None,
                trial_started: None,
                is_active: true,
            },
            system: SystemConfig {
                auto_update: true,
                check_interval: 24,
                logs_enabled: true,
                max_log_size: 10,
                analytics_enabled: false,
            },
        }
    }
}
