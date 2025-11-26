// Anti-Detection Module
// Browser fingerprint randomization and stealth techniques

use anyhow::Result;
use chromiumoxide::Page;
use rand::Rng;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Fingerprint {
    pub user_agent: String,
    pub screen_width: u32,
    pub screen_height: u32,
    pub locale: String,
    pub timezone: String,
    pub platform: String,
    pub vendor: String,
    pub webgl_vendor: String,
    pub webgl_renderer: String,
    pub color_depth: u8,
    pub device_memory: u8,
    pub hardware_concurrency: u8,
}

pub struct AntiDetection;

impl AntiDetection {
    pub fn new() -> Self {
        Self
    }

    pub fn generate_fingerprint(&self) -> Fingerprint {
        let mut rng = rand::thread_rng();

        let user_agents = vec![
            // Transparent User-Agent for ethical scraping
            "Mozilla/5.0 (compatible; TikTrendFinder/1.0; +https://tiktrendfinder.com/bot) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        ];

        let screens = vec![
            (1920, 1080),
            (1366, 768),
            (1536, 864),
            (1440, 900),
            (2560, 1440),
        ];

        let screen_idx = rng.gen_range(0..screens.len());
        let screen = screens[screen_idx];

        let ua_idx = rng.gen_range(0..user_agents.len());
        let user_agent = user_agents[ua_idx].to_string();

        Fingerprint {
            user_agent: user_agent.clone(),
            screen_width: screen.0,
            screen_height: screen.1,
            locale: "pt-BR".to_string(),
            timezone: "America/Sao_Paulo".to_string(),
            platform: if user_agent.contains("Windows") {
                "Win32"
            } else if user_agent.contains("Mac") {
                "MacIntel"
            } else {
                "Linux x86_64"
            }
            .to_string(),
            vendor: "Google Inc.".to_string(),
            webgl_vendor: "Google Inc. (NVIDIA)".to_string(),
            webgl_renderer: "ANGLE (NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0)".to_string(),
            color_depth: if rng.gen_bool(0.5) { 24 } else { 32 },
            device_memory: *vec![4, 8, 16].get(rng.gen_range(0..3)).unwrap(),
            hardware_concurrency: *vec![4, 8, 12, 16].get(rng.gen_range(0..4)).unwrap(),
        }
    }

    pub async fn inject_stealth_scripts(
        &self,
        page: &Page,
        fingerprint: Option<&Fingerprint>,
    ) -> Result<()> {
        // Main stealth script
        page.evaluate(Self::get_stealth_script()).await?;

        if let Some(fp) = fingerprint {
            let script = format!(
                r#"
                Object.defineProperty(navigator, 'userAgent', {{ get: () => '{}' }});
                Object.defineProperty(navigator, 'platform', {{ get: () => '{}' }});
                Object.defineProperty(navigator, 'language', {{ get: () => '{}' }});
                Object.defineProperty(navigator, 'languages', {{ get: () => ['{}', 'en-US'] }});
                Object.defineProperty(screen, 'width', {{ get: () => {} }});
                Object.defineProperty(screen, 'height', {{ get: () => {} }});
                Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => {} }});
                Object.defineProperty(navigator, 'deviceMemory', {{ get: () => {} }});
                Object.defineProperty(navigator, 'webdriver', {{ get: () => false }});
                // Mock plugins to look like a regular browser
                Object.defineProperty(navigator, 'plugins', {{ get: () => [
                    {{ name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' }},
                    {{ name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' }},
                    {{ name: 'Native Client', filename: 'internal-nacl-plugin', description: '' }}
                ] }});
            "#,
                fp.user_agent,
                fp.platform,
                fp.locale,
                fp.locale,
                fp.screen_width,
                fp.screen_height,
                fp.hardware_concurrency,
                fp.device_memory
            );

            page.evaluate(script).await?;
        }

        log::debug!("Injected stealth scripts");
        Ok(())
    }

    fn get_stealth_script() -> &'static str {
        r#"
        // Override webdriver flag
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
            configurable: true
        });
        
        // Override plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => {
                const plugins = [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
                ];
                const pluginArray = [];
                plugins.forEach((p, i) => {
                    pluginArray[i] = p;
                    pluginArray[p.name] = p;
                });
                pluginArray.length = plugins.length;
                return pluginArray;
            },
            configurable: true
        });
        
        // Override languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['pt-BR', 'pt', 'en-US', 'en'],
            configurable: true
        });
        
        // Canvas randomization
        const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
        CanvasRenderingContext2D.prototype.getImageData = function(...args) {
            const imageData = originalGetImageData.apply(this, args);
            for (let i = 0; i < imageData.data.length; i += 4) {
                imageData.data[i] += Math.floor(Math.random() * 3) - 1;
                imageData.data[i + 1] += Math.floor(Math.random() * 3) - 1;
                imageData.data[i + 2] += Math.floor(Math.random() * 3) - 1;
            }
            return imageData;
        };
        
        // WebGL fingerprint protection
        const getParameterProxyHandler = {
            apply: function(target, thisArg, args) {
                const param = args[0];
                if (param === 37445) return 'Google Inc. (NVIDIA)';
                if (param === 37446) return 'ANGLE (NVIDIA GeForce GTX 1080 Direct3D11 vs_5_0 ps_5_0)';
                return Reflect.apply(target, thisArg, args);
            }
        };
        
        // Override chrome object
        if (!window.chrome) {
            window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {}, app: {} };
        }
        
        // Remove automation indicators
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
        delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        
        console.log('[Stealth] Anti-detection loaded');
        "#
    }
}

impl Default for AntiDetection {
    fn default() -> Self {
        Self::new()
    }
}
