use crate::scraper::browser::BrowserManager;
use anyhow::Result;
use std::sync::Arc;

#[allow(dead_code)]
pub struct BrowserPool {
    browsers: Vec<Arc<BrowserManager>>,
    max_browsers: usize,
    headless: bool,
}

#[allow(dead_code)]
impl BrowserPool {
    pub fn new(max_browsers: usize, headless: bool) -> Self {
        Self {
            browsers: Vec::new(),
            max_browsers,
            headless,
        }
    }

    pub async fn get_browser(&mut self) -> Result<Arc<BrowserManager>> {
        // Simple round-robin or just create new if not full
        // For now, just create a new one if we haven't reached max
        if self.browsers.len() < self.max_browsers {
            let manager = BrowserManager::new(self.headless);
            manager.start(None).await?;
            let manager = Arc::new(manager);
            self.browsers.push(manager.clone());
            return Ok(manager);
        }

        // Return a random existing browser
        // In a real pool, we would track availability
        Ok(self.browsers[0].clone())
    }

    pub async fn shutdown(&mut self) -> Result<()> {
        for browser in &self.browsers {
            browser.stop().await?;
        }
        self.browsers.clear();
        Ok(())
    }
}
