// TikTok Parser Module
// HTML/JSON parsing for TikTok Shop pages

use anyhow::{Result, Context};
use chromiumoxide::Page;
use serde_json::Value;
use scraper::{Html, Selector};
use uuid::Uuid;

use crate::models::Product;

pub struct TikTokParser;

impl TikTokParser {
    pub fn new() -> Self {
        Self
    }

    pub async fn parse_product_list(&self, page: &Page) -> Result<Vec<Product>> {
        // Try JavaScript first (faster and more reliable)
        log::debug!("Attempting to parse products from __INITIAL_STATE__");
        
        let script = r#"
            (() => {
                if (window.__INITIAL_STATE__ && window.__INITIAL_STATE__.products) {
                    return JSON.stringify(window.__INITIAL_STATE__.products);
                }
                if (window.__INITIAL_STATE__ && window.__INITIAL_STATE__.productList) {
                    return JSON.stringify(window.__INITIAL_STATE__.productList.products || []);
                }
                return null;
            })()
        "#;
        
        let result = page.evaluate(script).await?;
        
        if let Some(json_str) = result.value() {
            if !json_str.is_null() {
                if let Ok(json_text) = serde_json::from_value::<String>(json_str.clone()) {
                    if let Ok(products_json) = serde_json::from_str::<Value>(&json_text) {
                        if let Some(arr) = products_json.as_array() {
                            let products: Vec<Product> = arr.iter()
                                .filter_map(|item| self.parse_product_json(item).ok())
                                .collect();
                            
                            if !products.is_empty() {
                                log::info!("Parsed {} products from JSON", products.len());
                                return Ok(products);
                            }
                        }
                    }
                }
            }
        }
        
        // Fallback to DOM parsing
        log::debug!("Falling back to DOM parsing");
        self.parse_product_list_from_dom(page).await
    }

    async fn parse_product_list_from_dom(&self, page: &Page) -> Result<Vec<Product>> {
        let html = page.content().await?;
        let document = Html::parse_document(&html);
        
        let selectors = vec![
            "[data-e2e='product-card']",
            ".product-card",
            ".product-item",
        ];
        
        for selector_str in &selectors {
            if let Ok(selector) = Selector::parse(selector_str) {
                let elements: Vec<_> = document.select(&selector).collect();
                
                if !elements.is_empty() {
                    log::debug!("Found {} products with selector: {}", elements.len(), selector_str);
                    
                    let products: Vec<Product> = elements.iter()
                        .filter_map(|element| {
                            self.parse_product_element(element).ok()
                        })
                        .collect();
                    
                    if !products.is_empty() {
                        return Ok(products);
                    }
                }
            }
        }
        
        log::warn!("No products found in DOM");
        Ok(Vec::new())
    }

    fn parse_product_json(&self, data: &Value) -> Result<Product> {
        let tiktok_id = data.get("id")
            .or_else(|| data.get("productId"))
            .or_else(|| data.get("product_id"))
            .and_then(|v| v.as_str().or_else(|| v.as_i64().map(|n| Box::leak(n.to_string().into_boxed_str()) as &str)))
            .context("Missing product ID")?
            .to_string();
        
        let title = data.get("title")
            .or_else(|| data.get("name"))
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();
        
        let price = self.extract_price(data.get("price"))?;
        let original_price_val = self.extract_price(data.get("originalPrice").or_else(|| data.get("original_price"))).ok();
        
        let currency = data.get("currency")
            .and_then(|v| v.as_str())
            .unwrap_or("BRL")
            .to_string();
        
        Ok(Product {
            id: Uuid::new_v4().to_string(),
            tiktok_id: tiktok_id.clone(),
            title,
            description: data.get("description").and_then(|v| v.as_str()).map(String::from),
            price,
            original_price: original_price_val,
            currency,
            category: data.get("category").and_then(|v| v.as_str()).map(String::from),
            subcategory: data.get("subcategory").and_then(|v| v.as_str()).map(String::from),
            seller_name: data.get("seller").and_then(|v| v.get("name")).and_then(|v| v.as_str()).map(String::from),
            seller_rating: data.get("seller").and_then(|v| v.get("rating")).and_then(|v| v.as_f64()),
            product_rating: data.get("rating").and_then(|v| Self::extract_rating(v)),
            reviews_count: data.get("reviewCount").and_then(|v| v.as_i64()).unwrap_or(0) as i32,
            sales_count: self.parse_sales_count(data.get("salesCount"))?,
            sales_7d: self.parse_sales_count(data.get("sales7d"))?,
            sales_30d: self.parse_sales_count(data.get("sales30d"))?,
            commission_rate: data.get("commissionRate").and_then(|v| v.as_f64()),
            image_url: data.get("imageUrl").or_else(|| data.get("image")).and_then(|v| v.as_str()).map(String::from),
            images: data.get("images").and_then(|v| v.as_array()).map(|arr| arr.iter().filter_map(|v| v.as_str().map(String::from)).collect()).unwrap_or_default(),
            video_url: data.get("videoUrl").and_then(|v| v.as_str()).map(String::from),
            product_url: data.get("url").and_then(|v| v.as_str()).map(String::from).unwrap_or_else(|| format!("https://shop.tiktok.com/product/{}", &tiktok_id)),
            affiliate_url: data.get("affiliateUrl").and_then(|v| v.as_str()).map(String::from),
            has_free_shipping: data.get("freeShipping").and_then(|v| v.as_bool()).unwrap_or(false),
            is_trending: data.get("isTrending").and_then(|v| v.as_bool()).unwrap_or(false),
            is_on_sale: original_price_val.map_or(false, |op| op > price),
            in_stock: data.get("inStock").and_then(|v| v.as_bool()).unwrap_or(true),
            collected_at: chrono::Utc::now().to_rfc3339(),
            updated_at: chrono::Utc::now().to_rfc3339(),
        })
    }

    fn parse_product_element(&self, element: &scraper::ElementRef) -> Result<Product> {
        let title_selector = Selector::parse("[data-e2e='product-title'], .product-title, h3, h4").ok();
        let title = if let Some(sel) = title_selector {
            element.select(&sel).next()
                .map(|e| e.text().collect::<String>().trim().to_string())
                .unwrap_or_default()
        } else {
            String::new()
        };
        
        let price_selector = Selector::parse("[data-e2e='product-price'], .product-price, .price").ok();
        let price_text = if let Some(sel) = price_selector {
            element.select(&sel).next()
                .map(|e| e.text().collect::<String>())
                .unwrap_or_else(|| "0".to_string())
        } else {
            "0".to_string()
        };
        let price = Self::parse_price_text(&price_text);
        
        let image_selector = Selector::parse("img").ok();
        let image_url = if let Some(sel) = image_selector {
            element.select(&sel).next()
                .and_then(|e| e.value().attr("src"))
                .map(String::from)
        } else {
            None
        };
        
        let link_selector = Selector::parse("a").ok();
        let product_url = if let Some(sel) = link_selector {
            element.select(&sel).next()
                .and_then(|e| e.value().attr("href"))
                .map(String::from)
                .unwrap_or_default()
        } else {
            String::new()
        };
        
        let tiktok_id = Self::extract_id_from_url(&product_url)
            .unwrap_or_else(|| Uuid::new_v4().to_string());
        
        Ok(Product {
            id: Uuid::new_v4().to_string(),
            tiktok_id,
            title,
            description: None,
            price,
            original_price: None,
            currency: "BRL".to_string(),
            category: None,
            subcategory: None,
            seller_name: None,
            seller_rating: None,
            product_rating: None,
            reviews_count: 0,
            sales_count: 0,
            sales_7d: 0,
            sales_30d: 0,
            commission_rate: None,
            image_url,
            images: vec![],
            video_url: None,
            product_url,
            affiliate_url: None,
            has_free_shipping: false,
            is_trending: false,
            is_on_sale: false,
            in_stock: true,
            collected_at: chrono::Utc::now().to_rfc3339(),
            updated_at: chrono::Utc::now().to_rfc3339(),
        })
    }

    fn extract_price(&self, value: Option<&Value>) -> Result<f64> {
        if let Some(v) = value {
            if let Some(num) = v.as_f64() {
                return Ok(num);
            }
            if let Some(s) = v.as_str() {
                return Ok(Self::parse_price_text(s));
            }
            if let Some(obj) = v.as_object() {
                if let Some(val) = obj.get("value").and_then(|v| v.as_f64()) {
                    return Ok(val);
                }
            }
        }
        Ok(0.0)
    }

    fn parse_price_text(text: &str) -> f64 {
        let cleaned = text
            .chars()
            .filter(|c| c.is_ascii_digit() || *c == ',' || *c == '.')
            .collect::<String>();
        
        let normalized = cleaned.replace(',', ".");
        normalized.parse().unwrap_or(0.0)
    }

    fn parse_sales_count(&self, value: Option<&Value>) -> Result<i32> {
        if let Some(v) = value {
            if let Some(num) = v.as_i64() {
                return Ok(num as i32);
            }
            if let Some(s) = v.as_str() {
                return Ok(Self::parse_sales_text(s));
            }
        }
        Ok(0)
    }

    fn parse_sales_text(text: &str) -> i32 {
        let text_lower = text.to_lowercase();
        
        if text_lower.contains('k') {
            if let Ok(num) = text_lower.trim_end_matches('k').parse::<f64>() {
                return (num * 1000.0) as i32;
            }
        }
        
        if text_lower.contains('m') {
            if let Ok(num) = text_lower.trim_end_matches('m').parse::<f64>() {
                return (num * 1000000.0) as i32;
            }
        }
        
        let digits: String = text.chars().filter(|c| c.is_ascii_digit()).collect();
        digits.parse().unwrap_or(0)
    }

    fn extract_rating(value: &Value) -> Option<f64> {
        if let Some(num) = value.as_f64() {
            if num >= 0.0 && num <= 5.0 {
                return Some(num);
            }
        }
        if let Some(obj) = value.as_object() {
            if let Some(avg) = obj.get("average").and_then(|v| v.as_f64()) {
                return Some(avg);
            }
        }
        None
    }

    fn extract_id_from_url(url: &str) -> Option<String> {
        use regex::Regex;
        let re = Regex::new(r"/product/(\d+)").ok()?;
        re.captures(url)
            .and_then(|cap| cap.get(1))
            .map(|m| m.as_str().to_string())
    }
}

impl Default for TikTokParser {
    fn default() -> Self {
        Self::new()
    }
}
