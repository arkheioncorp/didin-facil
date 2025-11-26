// Browser Manager Module
// Manages Chromium browser instances using chromiumoxide

use anyhow::{Context, Result};
use chromiumoxide::browser::{Browser, BrowserConfig};
use chromiumoxide::layout::Point;
use chromiumoxide::Page;
use futures::StreamExt;
use rand::Rng;
use std::path::PathBuf;
use std::sync::Arc;
use tokio::sync::Mutex;

pub struct BrowserManager {
    browser: Arc<Mutex<Option<Browser>>>,
    headless: bool,
    timeout_secs: u64,
    user_data_dir: Option<PathBuf>,
}

impl BrowserManager {
    pub fn new(headless: bool) -> Self {
        Self {
            browser: Arc::new(Mutex::new(None)),
            headless,
            timeout_secs: 30,
            user_data_dir: None,
        }
    }

    pub fn with_timeout(mut self, timeout: u64) -> Self {
        self.timeout_secs = timeout;
        self
    }

    pub fn with_user_data(mut self, path: PathBuf) -> Self {
        self.user_data_dir = Some(path);
        self
    }

    pub async fn start(&self, proxy: Option<String>) -> Result<()> {
        log::info!(
            "Starting browser (headless: {}, proxy: {:?})...",
            self.headless,
            proxy
        );

        let mut builder = BrowserConfig::builder().args(vec![
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
        ]);

        // Browser arguments for stealth
        let mut args = vec![
            "--disable-blink-features=AutomationControlled",
            "--disable-accelerated-2d-canvas",
            "--window-size=1920,1080",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
        ];

        if let Some(proxy_url) = proxy {
            args.push(Box::leak(
                format!("--proxy-server={}", proxy_url).into_boxed_str(),
            ));
        }

        builder = builder.args(args);

        if !self.headless {
            builder = builder.with_head();
        }

        if let Some(dir) = &self.user_data_dir {
            builder = builder.user_data_dir(dir);
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
        let browser = browser.as_ref().context("Browser not started")?;

        let page = browser
            .new_page("about:blank")
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
        }
        Ok(())
    }

    #[allow(dead_code)]
    pub async fn is_running(&self) -> bool {
        self.browser.lock().await.is_some()
    }

    pub async fn simulate_human_interaction(&self, page: &Page) -> Result<()> {
        let width = 1920;
        let height = 1080;

        for _ in 0..3 {
            let (x, y) = {
                let mut rng = rand::thread_rng();
                (rng.gen_range(0..width), rng.gen_range(0..height))
            };

            page.move_mouse(Point::new(x as f64, y as f64)).await?;

            let delay = { rand::thread_rng().gen_range(100..300) };
            tokio::time::sleep(tokio::time::Duration::from_millis(delay)).await;
        }
        Ok(())
    }
}

impl Drop for BrowserManager {
    fn drop(&mut self) {
        log::debug!("Dropping BrowserManager - ensuring cleanup");
        // The Arc<Mutex<Option<Browser>>> will be dropped.
        // If this is the last reference, the Browser will be dropped and closed.
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_browser_lifecycle() {
        let manager = BrowserManager::new(true);

        assert!(!manager.is_running().await);

        manager.start(None).await.expect("Failed to start browser");
        assert!(manager.is_running().await);

        let page = manager.new_page().await.expect("Failed to create page");
        assert!(page.url().await.is_ok());

        manager.stop().await.expect("Failed to stop browser");
        assert!(!manager.is_running().await);
    }
}
