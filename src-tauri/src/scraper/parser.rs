// TikTok Parser Module
// HTML/JSON parsing for TikTok Shop pages

use anyhow::{Context, Result};
use chromiumoxide::Page;
use scraper::{Html, Selector};
use serde_json::Value;
use uuid::Uuid;

use crate::models::Product;

pub struct TikTokParser {
    selectors: Vec<String>,
}

impl TikTokParser {
    pub fn new(selectors: Option<Vec<String>>) -> Self {
        Self {
            selectors: selectors.unwrap_or_else(|| {
                vec![
                    "[data-e2e='product-card']".to_string(),
                    ".product-card".to_string(),
                    ".product-item".to_string(),
                ]
            }),
        }
    }

    pub async fn parse_product_list(&self, page: &Page) -> Result<Vec<Product>> {
        // Try JavaScript first (faster and more reliable)
        log::debug!("Attempting to parse products from __INITIAL_STATE__");

        let script = r#"
            (() => {
                if (window.__INITIAL_STATE__) {
                    // Direct product list
                    if (window.__INITIAL_STATE__.products) {
                        return JSON.stringify(window.__INITIAL_STATE__.products);
                    }
                    // Product list wrapper
                    if (window.__INITIAL_STATE__.productList && window.__INITIAL_STATE__.productList.products) {
                        return JSON.stringify(window.__INITIAL_STATE__.productList.products);
                    }
                    // Shop page structure
                    if (window.__INITIAL_STATE__.shop && window.__INITIAL_STATE__.shop.products) {
                        return JSON.stringify(window.__INITIAL_STATE__.shop.products);
                    }
                    // General search result
                    if (window.__INITIAL_STATE__.search && window.__INITIAL_STATE__.search.item_list) {
                        return JSON.stringify(window.__INITIAL_STATE__.search.item_list);
                    }
                }
                
                // Try to find JSON in script tags (SIGI_STATE is common in TikTok)
                const sigiState = document.getElementById('SIGI_STATE');
                if (sigiState) {
                    try {
                        const data = JSON.parse(sigiState.textContent);
                        if (data.ItemModule) {
                            return JSON.stringify(Object.values(data.ItemModule));
                        }
                    } catch (e) {}
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
                            let products: Vec<Product> = arr
                                .iter()
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

        for selector_str in &self.selectors {
            if let Ok(selector) = Selector::parse(selector_str) {
                let elements: Vec<_> = document.select(&selector).collect();

                if !elements.is_empty() {
                    log::debug!(
                        "Found {} products with selector: {}",
                        elements.len(),
                        selector_str
                    );

                    let products: Vec<Product> = elements
                        .iter()
                        .filter_map(|element| self.parse_product_element(element).ok())
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
        let tiktok_id = data
            .get("id")
            .or_else(|| data.get("productId"))
            .or_else(|| data.get("product_id"))
            .and_then(|v| {
                v.as_str().or_else(|| {
                    v.as_i64()
                        .map(|n| Box::leak(n.to_string().into_boxed_str()) as &str)
                })
            })
            .context("Missing product ID")?
            .to_string();

        let title = data
            .get("title")
            .or_else(|| data.get("name"))
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();

        let price = self.extract_price(data.get("price"))?;
        let original_price_val = self
            .extract_price(
                data.get("originalPrice")
                    .or_else(|| data.get("original_price")),
            )
            .ok();

        let currency = data
            .get("currency")
            .and_then(|v| v.as_str())
            .unwrap_or("BRL")
            .to_string();

        Ok(Product {
            id: Uuid::new_v4().to_string(),
            tiktok_id: tiktok_id.clone(),
            title,
            description: data
                .get("description")
                .and_then(|v| v.as_str())
                .map(String::from),
            price,
            original_price: original_price_val,
            currency,
            category: data
                .get("category")
                .and_then(|v| v.as_str())
                .map(String::from),
            subcategory: data
                .get("subcategory")
                .and_then(|v| v.as_str())
                .map(String::from),
            seller_name: data
                .get("seller")
                .and_then(|v| v.get("name"))
                .and_then(|v| v.as_str())
                .map(String::from),
            seller_rating: data
                .get("seller")
                .and_then(|v| v.get("rating"))
                .and_then(|v| v.as_f64()),
            product_rating: data.get("rating").and_then(|v| Self::extract_rating(v)),
            reviews_count: data
                .get("reviewCount")
                .and_then(|v| v.as_i64())
                .unwrap_or(0) as i32,
            sales_count: self.parse_sales_count(data.get("salesCount"))?,
            sales_7d: self.parse_sales_count(data.get("sales7d"))?,
            sales_30d: self.parse_sales_count(data.get("sales30d"))?,
            commission_rate: data.get("commissionRate").and_then(|v| v.as_f64()),
            image_url: data
                .get("imageUrl")
                .or_else(|| data.get("image"))
                .and_then(|v| v.as_str())
                .map(String::from),
            images: data
                .get("images")
                .and_then(|v| v.as_array())
                .map(|arr| {
                    arr.iter()
                        .filter_map(|v| v.as_str().map(String::from))
                        .collect()
                })
                .unwrap_or_default(),
            video_url: data
                .get("videoUrl")
                .and_then(|v| v.as_str())
                .map(String::from),
            product_url: data
                .get("url")
                .and_then(|v| v.as_str())
                .map(String::from)
                .unwrap_or_else(|| format!("https://shop.tiktok.com/product/{}", &tiktok_id)),
            affiliate_url: data
                .get("affiliateUrl")
                .and_then(|v| v.as_str())
                .map(String::from),
            has_free_shipping: data
                .get("freeShipping")
                .and_then(|v| v.as_bool())
                .unwrap_or(false),
            is_trending: data
                .get("isTrending")
                .and_then(|v| v.as_bool())
                .unwrap_or(false),
            is_on_sale: original_price_val.map_or(false, |op| op > price),
            in_stock: data
                .get("inStock")
                .and_then(|v| v.as_bool())
                .unwrap_or(true),
            stock_level: data
                .get("stock")
                .or_else(|| data.get("stockLevel"))
                .or_else(|| data.get("quantity"))
                .and_then(|v| v.as_i64())
                .map(|v| v as i32),
            collected_at: chrono::Utc::now().to_rfc3339(),
            updated_at: chrono::Utc::now().to_rfc3339(),
        })
    }

    fn parse_product_element(&self, element: &scraper::ElementRef) -> Result<Product> {
        let title_selector =
            Selector::parse("[data-e2e='product-title'], .product-title, h3, h4").ok();
        let title = if let Some(sel) = title_selector {
            element
                .select(&sel)
                .next()
                .map(|e| e.text().collect::<String>().trim().to_string())
                .unwrap_or_default()
        } else {
            String::new()
        };

        let price_selector =
            Selector::parse("[data-e2e='product-price'], .product-price, .price").ok();
        let price_text = if let Some(sel) = price_selector {
            element
                .select(&sel)
                .next()
                .map(|e| e.text().collect::<String>())
                .unwrap_or_else(|| "0".to_string())
        } else {
            "0".to_string()
        };
        let price = Self::parse_price_text(&price_text);

        let image_selector = Selector::parse("img").ok();
        let image_url = if let Some(sel) = image_selector {
            element
                .select(&sel)
                .next()
                .and_then(|e| e.value().attr("src"))
                .map(String::from)
        } else {
            None
        };

        let link_selector = Selector::parse("a").ok();
        let product_url = if let Some(sel) = link_selector {
            element
                .select(&sel)
                .next()
                .and_then(|e| e.value().attr("href"))
                .map(String::from)
                .unwrap_or_default()
        } else {
            String::new()
        };

        let tiktok_id =
            Self::extract_id_from_url(&product_url).unwrap_or_else(|| Uuid::new_v4().to_string());

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
            stock_level: None,
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
        // Keep only digits, comma, dot
        let cleaned: String = text
            .chars()
            .filter(|c| c.is_ascii_digit() || *c == ',' || *c == '.')
            .collect();

        if cleaned.is_empty() {
            return 0.0;
        }

        // Check for multiple separators to determine format
        let last_comma = cleaned.rfind(',');
        let last_dot = cleaned.rfind('.');

        let normalized = match (last_comma, last_dot) {
            (Some(c), Some(d)) => {
                if c > d {
                    // Format: 1.234,56 (BR/EU) -> Remove dots, replace comma with dot
                    cleaned.replace('.', "").replace(',', ".")
                } else {
                    // Format: 1,234.56 (US) -> Remove commas
                    cleaned.replace(',', "")
                }
            }
            (Some(_), None) => {
                // Format: 1234,56 (BR/EU) -> Replace comma with dot
                cleaned.replace(',', ".")
            }
            (None, Some(d)) => {
                // Format: 1234.56 or 1.234.567
                let dot_count = cleaned.matches('.').count();
                if dot_count > 1 {
                    // Multiple dots = thousands separators (1.234.567)
                    cleaned.replace('.', "")
                } else if cleaned.len() - d - 1 == 3 {
                    // One dot, 3 digits after = likely thousands (1.234)
                    // This is a heuristic, but safe for TikTok BR context
                    cleaned.replace('.', "")
                } else {
                    // One dot, not 3 digits = decimal (1.23)
                    cleaned
                }
            }
            (None, None) => cleaned,
        };

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

        // Check for suffixes
        let multiplier = if text_lower.contains('k') {
            1000.0
        } else if text_lower.contains('m') {
            1000000.0
        } else {
            1.0
        };

        if multiplier > 1.0 {
            // Handle 1.5k or 1,5k
            let num_part = text_lower
                .trim_end_matches('k')
                .trim_end_matches('m')
                .trim()
                .replace(',', "."); // Normalize decimal separator

            if let Ok(val) = num_part.parse::<f64>() {
                return (val * multiplier) as i32;
            }
        }

        // Fallback: extract all digits (handles 1.234 as 1234)
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
        Self::new(None)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn test_parse_stock_level() {
        let parser = TikTokParser::default();

        // Case 1: "stock" field
        let data = json!({
            "id": "123",
            "title": "Test Product",
            "price": 10.0,
            "stock": 100
        });
        let product = parser.parse_product_json(&data).unwrap();
        assert_eq!(product.stock_level, Some(100));

        // Case 2: "stockLevel" field
        let data = json!({
            "id": "124",
            "title": "Test Product 2",
            "price": 10.0,
            "stockLevel": 50
        });
        let product = parser.parse_product_json(&data).unwrap();
        assert_eq!(product.stock_level, Some(50));

        // Case 3: "quantity" field
        let data = json!({
            "id": "125",
            "title": "Test Product 3",
            "price": 10.0,
            "quantity": 25
        });
        let product = parser.parse_product_json(&data).unwrap();
        assert_eq!(product.stock_level, Some(25));

        // Case 4: No stock info
        let data = json!({
            "id": "126",
            "title": "Test Product 4",
            "price": 10.0
        });
        let product = parser.parse_product_json(&data).unwrap();
        assert_eq!(product.stock_level, None);
    }
}
