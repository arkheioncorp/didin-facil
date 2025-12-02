// Models for TikTrend Finder
use serde::{Deserialize, Serialize};
use ts_rs::TS;

// ==================================================
// SUBSCRIPTION & PLAN MODELS (SaaS Híbrido)
// ==================================================

/// Plan tier enum
#[derive(Debug, Clone, Serialize, Deserialize, TS, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub enum PlanTier {
    Free,
    Starter,
    Business,
    Enterprise,
}

impl Default for PlanTier {
    fn default() -> Self {
        PlanTier::Free
    }
}

/// Execution mode enum
#[derive(Debug, Clone, Serialize, Deserialize, TS, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub enum ExecutionMode {
    WebOnly,
    Hybrid,
    LocalFirst,
}

impl Default for ExecutionMode {
    fn default() -> Self {
        ExecutionMode::WebOnly
    }
}

/// Subscription status enum
#[derive(Debug, Clone, Serialize, Deserialize, TS, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub enum SubscriptionStatus {
    Active,
    Trialing,
    PastDue,
    Canceled,
    Expired,
}

impl Default for SubscriptionStatus {
    fn default() -> Self {
        SubscriptionStatus::Active
    }
}

/// Marketplace access enum
#[derive(Debug, Clone, Serialize, Deserialize, TS, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub enum MarketplaceAccess {
    Tiktok,
    Aliexpress,
    Shopee,
    Amazon,
    Mercadolivre,
}

/// Full subscription info returned from API validation
#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct Subscription {
    pub id: String,
    pub user_id: String,
    pub plan_tier: PlanTier,
    pub status: SubscriptionStatus,
    pub execution_mode: ExecutionMode,
    pub billing_cycle: String,
    pub current_period_start: String,
    pub current_period_end: String,
    pub marketplaces: Vec<MarketplaceAccess>,
    pub limits: SubscriptionLimits,
    pub features: SubscriptionFeatures,
    pub cached_at: String,
    pub offline_days_allowed: i32,
    pub grace_period_days: i32,
}

/// Subscription limits (metered features)
#[derive(Debug, Clone, Serialize, Deserialize, TS, Default)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct SubscriptionLimits {
    pub price_searches: i32,
    pub favorites: i32,
    pub whatsapp_messages: i32,
    pub api_calls: i32,
    pub crm_leads: i32,
    pub chatbot_flows: i32,
    pub social_posts: i32,
}

/// Subscription features (boolean toggles)
#[derive(Debug, Clone, Serialize, Deserialize, TS, Default)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct SubscriptionFeatures {
    pub chatbot_ai: bool,
    pub analytics_advanced: bool,
    pub analytics_export: bool,
    pub crm_automation: bool,
    pub api_access: bool,
    pub offline_mode: bool,
    pub hybrid_sync: bool,
    pub priority_support: bool,
}

/// Cached subscription data for offline validation
#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct CachedSubscription {
    pub subscription: Subscription,
    pub cached_at: String,
    pub valid_until: String,
    pub last_sync: String,
}

/// Validation result from API
#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct SubscriptionValidation {
    pub is_valid: bool,
    pub subscription: Option<Subscription>,
    pub reason: Option<String>,
    pub message: Option<String>,
}

// ==================================================
// LEGACY LICENSE MODEL (backwards compatibility)
// ==================================================

#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct Product {
    pub id: String,
    pub tiktok_id: String,
    pub title: String,
    pub description: Option<String>,
    pub price: f64,
    pub original_price: Option<f64>,
    pub currency: String,
    pub category: Option<String>,
    pub subcategory: Option<String>,
    pub seller_name: Option<String>,
    pub seller_rating: Option<f64>,
    pub product_rating: Option<f64>,
    pub reviews_count: i32,
    pub sales_count: i32,
    pub sales_7d: i32,
    pub sales_30d: i32,
    pub commission_rate: Option<f64>,
    pub image_url: Option<String>,
    pub images: Vec<String>,
    pub video_url: Option<String>,
    pub product_url: String,
    pub affiliate_url: Option<String>,
    pub has_free_shipping: bool,
    pub is_trending: bool,
    pub is_on_sale: bool,
    pub in_stock: bool,
    pub stock_level: Option<i32>,
    pub collected_at: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct ProductHistory {
    pub id: String,
    pub product_id: String,
    pub price: f64,
    pub sales_count: i32,
    pub stock_level: Option<i32>,
    pub collected_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct SearchFilters {
    pub query: Option<String>,
    pub categories: Vec<String>,
    pub price_min: Option<f64>,
    pub price_max: Option<f64>,
    pub sales_min: Option<i32>,
    pub rating_min: Option<f64>,
    pub has_free_shipping: Option<bool>,
    pub is_trending: Option<bool>,
    pub is_on_sale: Option<bool>,
    pub sort_by: Option<String>,
    pub sort_order: Option<String>,
    pub page: Option<i32>,
    pub page_size: Option<i32>,
}

#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts", bound = "T: TS")]
pub struct PaginatedResponse<T> {
    pub data: Vec<T>,
    pub total: i64,
    pub page: i32,
    pub page_size: i32,
    pub has_more: bool,
}

#[allow(dead_code)]
#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct User {
    pub id: String,
    pub email: String,
    pub name: Option<String>,
    pub plan: String,
    pub plan_expires_at: String,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct License {
    pub is_valid: bool,
    pub plan: String,  // "lifetime" or "trial"
    pub features: PlanFeatures,
    pub expires_at: String,  // Empty = lifetime (never expires)
    pub credits: i32,  // Créditos IA disponíveis
}

#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct PlanFeatures {
    pub searches_unlimited: bool,  // Lifetime = true
    pub favorites_unlimited: bool,  // Lifetime = true
    pub export_enabled: bool,
    pub scheduler_enabled: bool,
}

// Deprecated - keeping for backwards compatibility
#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct UsageStats {
    pub credits_used: i32,
    pub credits_remaining: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct DashboardStats {
    pub total_products: i64,
    pub trending_products: i64,
    pub favorite_count: i64,
    pub searches_today: i64,
    pub copies_generated: i64,
    pub top_categories: Vec<CategoryCount>,
}

#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct CategoryCount {
    pub name: String,
    pub count: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct CopyRequest {
    pub product_id: String,
    pub copy_type: String,
    pub tone: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct CopyResponse {
    pub content: String,
    pub tokens_used: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct CopyHistory {
    pub id: String,
    pub user_id: String,
    pub product_id: Option<String>,
    pub copy_type: String,
    pub tone: String,
    pub content: String,
    pub tokens_used: i32,
    pub is_favorite: bool,
    pub created_at: String,
}

// ScraperConfig removed to use crate::config::ScraperConfig

#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct ScraperStatus {
    pub is_running: bool,
    pub progress: f32,
    pub current_product: Option<String>,
    pub products_found: i32,
    pub errors: Vec<String>,
    pub logs: Vec<String>,
    pub started_at: Option<String>,
    pub status_message: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct FavoriteList {
    pub id: String,
    pub user_id: String,
    pub name: String,
    pub description: Option<String>,
    pub color: String,
    pub icon: String,
    pub product_count: i32,
    pub created_at: String,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct FavoriteItem {
    pub id: String,
    pub user_id: String,
    pub product_id: String,
    pub list_id: Option<String>,
    pub notes: Option<String>,
    pub added_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct FavoriteWithProduct {
    pub favorite: FavoriteItem,
    pub product: Product,
}

#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct SearchHistoryItem {
    pub id: String,
    pub user_id: String,
    pub query: String,
    pub filters: String,
    pub results_count: i32,
    pub searched_at: String,
}

#[allow(dead_code)]
#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct CollectionLog {
    pub id: String,
    pub status: String,
    pub products_found: i32,
    pub products_saved: i32,
    pub errors_count: i32,
    pub duration_ms: i64,
    pub started_at: String,
    pub completed_at: Option<String>,
}

#[allow(dead_code)]
#[derive(Debug, Clone, Serialize, Deserialize, TS)]
#[serde(rename_all = "camelCase")]
#[ts(export, export_to = "../src/types/tauri-bindings.ts")]
pub struct FilterPreset {
    pub id: String,
    pub user_id: String,
    pub name: String,
    pub filters: String,
    pub usage_count: i32,
    pub created_at: String,
}
