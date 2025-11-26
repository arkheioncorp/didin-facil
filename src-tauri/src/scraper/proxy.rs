// Proxy Pool Module
// Rotating proxy management with health tracking

use chrono::{DateTime, Duration, Utc};
use regex::Regex;
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

use super::models::ProxyConfig;

#[derive(Debug, Clone, Default)]
#[allow(dead_code)]
pub struct ProxyStats {
    pub success_count: u32,
    pub failure_count: u32,
    pub total_requests: u32,
    pub last_used: Option<DateTime<Utc>>,
    pub is_blocked: bool,
    pub blocked_until: Option<DateTime<Utc>>,
}

#[allow(dead_code)]
pub struct ProxyPool {
    proxies: Vec<ProxyConfig>,
    stats: Arc<RwLock<HashMap<String, ProxyStats>>>,
    current_index: Arc<RwLock<usize>>,
}

#[allow(dead_code)]
impl ProxyPool {
    pub fn new(proxy_urls: Vec<String>) -> Self {
        let proxies: Vec<ProxyConfig> = proxy_urls
            .into_iter()
            .filter_map(|url| Self::parse_proxy_url(&url))
            .collect();

        let mut stats = HashMap::new();
        for proxy in &proxies {
            stats.insert(proxy.server.clone(), ProxyStats::default());
        }

        Self {
            proxies,
            stats: Arc::new(RwLock::new(stats)),
            current_index: Arc::new(RwLock::new(0)),
        }
    }

    fn parse_proxy_url(url: &str) -> Option<ProxyConfig> {
        // Regex to validate and parse proxy URL
        // Supports: protocol://user:pass@host:port or host:port or user:pass@host:port
        let re = Regex::new(r"^(?:(?P<protocol>\w+)://)?(?:(?P<user>[^:@]+):(?P<pass>[^:@]+)@)?(?P<host>[^:@]+):(?P<port>\d+)$").ok()?;

        let caps = re.captures(url)?;

        let host = caps.name("host")?.as_str();
        let port = caps.name("port")?.as_str();
        let protocol = caps.name("protocol").map_or("http", |m| m.as_str());

        let server = format!("{}://{}:{}", protocol, host, port);

        let username = caps.name("user").map(|m| m.as_str().to_string());
        let password = caps.name("pass").map(|m| m.as_str().to_string());

        Some(ProxyConfig {
            server,
            username,
            password,
        })
    }

    pub fn has_proxies(&self) -> bool {
        !self.proxies.is_empty()
    }

    async fn get_available(&self) -> Vec<ProxyConfig> {
        let now = Utc::now();
        let stats = self.stats.read().await;

        self.proxies
            .iter()
            .filter(|proxy| {
                stats
                    .get(&proxy.server)
                    .map(|s| !s.is_blocked || s.blocked_until.map_or(false, |t| now > t))
                    .unwrap_or(true)
            })
            .cloned()
            .collect()
    }

    pub async fn get_next(&self) -> Option<ProxyConfig> {
        let available = self.get_available().await;
        if available.is_empty() {
            return None;
        }

        let mut index = self.current_index.write().await;
        *index = (*index + 1) % available.len();

        let proxy = available[*index].clone();

        // Update stats
        let mut stats = self.stats.write().await;
        if let Some(s) = stats.get_mut(&proxy.server) {
            s.last_used = Some(Utc::now());
            s.total_requests += 1;
        }

        Some(proxy)
    }

    pub async fn report_success(&self, proxy: &ProxyConfig) {
        let mut stats = self.stats.write().await;
        if let Some(s) = stats.get_mut(&proxy.server) {
            s.success_count += 1;
            log::debug!(
                "Proxy {} success ({}/{})",
                proxy.server,
                s.success_count,
                s.total_requests
            );
        }
    }

    pub async fn report_failure(&self, proxy: &ProxyConfig, block_minutes: Option<i64>) {
        let mut stats = self.stats.write().await;
        if let Some(s) = stats.get_mut(&proxy.server) {
            s.failure_count += 1;

            let failure_rate = s.failure_count as f32 / s.total_requests.max(1) as f32;

            if failure_rate > 0.5 && s.total_requests >= 5 {
                let minutes = block_minutes.unwrap_or(30);
                s.is_blocked = true;
                s.blocked_until = Some(Utc::now() + Duration::minutes(minutes));
                log::warn!(
                    "Proxy {} blocked for {} minutes (failure rate: {:.1}%)",
                    proxy.server,
                    minutes,
                    failure_rate * 100.0
                );
            }
        }
    }

    pub async fn get_stats_summary(&self) -> HashMap<String, u32> {
        let stats = self.stats.read().await;
        let available = self.get_available().await;

        let total = self.proxies.len() as u32;
        let available_count = available.len() as u32;
        let blocked = total - available_count;

        let total_requests: u32 = stats.values().map(|s| s.total_requests).sum();
        let total_success: u32 = stats.values().map(|s| s.success_count).sum();

        HashMap::from([
            ("total".to_string(), total),
            ("available".to_string(), available_count),
            ("blocked".to_string(), blocked),
            ("requests".to_string(), total_requests),
            ("success".to_string(), total_success),
        ])
    }
}
