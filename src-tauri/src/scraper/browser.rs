// Browser Manager Module
// Manages Chromium browser instances using chromiumoxide

use anyhow::{Result, Context};
use chromiumoxide::browser::{Browser, BrowserConfig};
use chromiumoxide::Page;
use futures::StreamExt;
use std::sync::Arc;
use tokio::sync::Mutex;

pub struct BrowserManager {
    browser: Arc<Mutex<Option<Browser>>>,
    headless: bool,
}

impl BrowserManager {
    pub fn new(headless: bool) -> Self {
        Self {
            browser: Arc::new(Mutex::new(None)),
            headless,
        }
    }

    pub async fn start(&self, proxy: Option<String>) -> Result<()> {
        log::info!("Starting browser (headless: {}, proxy: {:?})...", self.headless, proxy);
        
        let mut builder = BrowserConfig::builder();
        
        // Browser arguments for stealth
        let mut args = vec![
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-accelerated-2d-canvas",
            "--disable-gpu",
            "--window-size=1920,1080",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
        ];

        if let Some(proxy_url) = proxy {
            args.push(Box::leak(format!("--proxy-server={}", proxy_url).into_boxed_str()));
        }
        
        builder = builder.args(args);
        
        if !self.headless {
            builder = builder.with_head();
        }
        
        let config = builder
            .build()
            .map_err(|e| anyhow::anyhow!("Failed to build browser config: {}", e))?;
        
        let (browser, mut handler) = Browser::launch(config)
            .await
            .context("Failed to launch browser")?;
        
        // Spawn task to handle browser events
        tokio::spawn(async move {
            while let Some(event) = handler.next().await {
                log::trace!("Browser event: {:?}", event);
            }
            log::debug!("Browser handler closed");
        });

        *self.browser.lock().await = Some(browser);
        log::info!("Browser started successfully");
        
        Ok(())
    }

    pub async fn new_page(&self) -> Result<Page> {
        let browser = self.browser.lock().await;
        let browser = browser.as_ref()
            .context("Browser not started")?;
        
        let page = browser.new_page("about:blank")
            .await
            .context("Failed to create new page")?;
        
        log::debug!("Created new browser page");
        Ok(page)
    }

    pub async fn stop(&self) -> Result<()> {
        let mut browser = self.browser.lock().await;
        
        if let Some(b) = browser.take() {
            // Browser will cleanup on drop
            drop(b);
            log::info!("Browser stopped");
        }
        
        Ok(())
    }

    pub async fn is_running(&self) -> bool {
        self.browser.lock().await.is_some()
    }
}

impl Drop for BrowserManager {
    fn drop(&mut self) {
        log::debug!("BrowserManager dropped");
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_browser_lifecycle() {
        let manager = BrowserManager::new(true);
        
        assert!(!manager.is_running().await);
        
        manager.start().await.expect("Failed to start browser");
        assert!(manager.is_running().await);
        
        let page = manager.new_page().await.expect("Failed to create page");
        assert!(page.url().await.is_ok());
        
        manager.stop().await.expect("Failed to stop browser");
        assert!(!manager.is_running().await);
    }
}
