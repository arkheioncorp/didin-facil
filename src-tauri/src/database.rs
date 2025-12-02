// Database module for SQLite operations
use crate::models::*;
use rusqlite::{params, Connection, OptionalExtension, Result};
use std::path::Path;
use uuid::Uuid;

pub fn init_database(db_path: &Path) -> Result<()> {
    let conn = Connection::open(db_path)?;

    conn.execute_batch(
        "
        -- Users table
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            name TEXT,
            plan TEXT NOT NULL DEFAULT 'trial',
            plan_expires_at TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        -- Products table
        CREATE TABLE IF NOT EXISTS products (
            id TEXT PRIMARY KEY,
            tiktok_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            original_price REAL,
            currency TEXT DEFAULT 'BRL',
            category TEXT,
            subcategory TEXT,
            seller_name TEXT,
            seller_rating REAL,
            product_rating REAL,
            reviews_count INTEGER DEFAULT 0,
            sales_count INTEGER DEFAULT 0,
            sales_7d INTEGER DEFAULT 0,
            sales_30d INTEGER DEFAULT 0,
            commission_rate REAL,
            image_url TEXT,
            images TEXT,
            video_url TEXT,
            product_url TEXT NOT NULL,
            affiliate_url TEXT,
            has_free_shipping INTEGER DEFAULT 0,
            is_trending INTEGER DEFAULT 0,
            is_on_sale INTEGER DEFAULT 0,
            in_stock INTEGER DEFAULT 1,
            stock_level INTEGER,
            collected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        -- Product history table
        CREATE TABLE IF NOT EXISTS product_history (
            id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            price REAL NOT NULL,
            sales_count INTEGER DEFAULT 0,
            stock_level INTEGER,
            collected_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        -- Indexes for products
        CREATE INDEX IF NOT EXISTS idx_products_collected_at ON products(collected_at);
        CREATE INDEX IF NOT EXISTS idx_products_sales_count ON products(sales_count);
        CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
        CREATE INDEX IF NOT EXISTS idx_products_rating ON products(product_rating);
        CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);

        -- Favorites table
        CREATE TABLE IF NOT EXISTS favorites (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            list_id TEXT,
            notes TEXT,
            added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id),
            UNIQUE(user_id, product_id)
        );

        -- Favorite lists table
        CREATE TABLE IF NOT EXISTS favorite_lists (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            color TEXT DEFAULT '#FF0050',
            icon TEXT DEFAULT 'heart',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        -- Copy history table
        CREATE TABLE IF NOT EXISTS copy_history (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            product_id TEXT,
            copy_type TEXT NOT NULL,
            tone TEXT NOT NULL,
            content TEXT NOT NULL,
            tokens_used INTEGER DEFAULT 0,
            is_favorite INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        -- Search history table
        CREATE TABLE IF NOT EXISTS search_history (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            query TEXT NOT NULL,
            filters TEXT,
            results_count INTEGER DEFAULT 0,
            searched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        -- Error pages table
        CREATE TABLE IF NOT EXISTS error_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            html TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        -- Profiles table
        CREATE TABLE IF NOT EXISTS profiles (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            cookies TEXT,
            user_agent TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        -- Filter presets table
        CREATE TABLE IF NOT EXISTS filter_presets (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            filters TEXT NOT NULL,
            usage_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        -- App settings table
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        -- Collection logs table
        CREATE TABLE IF NOT EXISTS collection_logs (
            id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            products_found INTEGER DEFAULT 0,
            products_saved INTEGER DEFAULT 0,
            errors_count INTEGER DEFAULT 0,
            duration_ms INTEGER DEFAULT 0,
            started_at TEXT NOT NULL,
            completed_at TEXT
        );

        -- Create indexes for better performance
        CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
        CREATE INDEX IF NOT EXISTS idx_products_trending ON products(is_trending);
        CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
        CREATE INDEX IF NOT EXISTS idx_products_sales ON products(sales_count);
        CREATE INDEX IF NOT EXISTS idx_products_collected ON products(collected_at);
        CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
        CREATE INDEX IF NOT EXISTS idx_favorites_product ON favorites(product_id);
        CREATE INDEX IF NOT EXISTS idx_search_history_user ON search_history(user_id);
        CREATE INDEX IF NOT EXISTS idx_copy_history_user ON copy_history(user_id);
        
        -- Insert default settings
        INSERT OR IGNORE INTO settings (key, value) VALUES ('theme', 'dark');
        INSERT OR IGNORE INTO settings (key, value) VALUES ('language', 'pt-BR');
        INSERT OR IGNORE INTO settings (key, value) VALUES ('notifications_enabled', 'true');
        INSERT OR IGNORE INTO settings (key, value) VALUES ('max_products_per_search', '50');
        ",
    )?;

    // Migration: Add stock_level column if it doesn't exist
    let _ = conn.execute("ALTER TABLE products ADD COLUMN stock_level INTEGER", []);

    log::info!("Database initialized successfully at {:?}", db_path);
    Ok(())
}

pub fn get_connection(db_path: &Path) -> Result<Connection> {
    Connection::open(db_path)
}

// ==========================================
// PRODUCT QUERIES
// ==========================================

pub fn search_products(
    db_path: &Path,
    filters: &SearchFilters,
) -> Result<PaginatedResponse<Product>> {
    let conn = get_connection(db_path)?;

    let mut query = String::from("SELECT * FROM products WHERE 1=1");
    let mut count_query = String::from("SELECT COUNT(*) FROM products WHERE 1=1");
    let mut params_vec: Vec<Box<dyn rusqlite::ToSql>> = Vec::new();

    // Build WHERE clauses
    if let Some(ref q) = filters.query {
        let search_clause = " AND (title LIKE ? OR description LIKE ? OR category LIKE ?)";
        query.push_str(search_clause);
        count_query.push_str(search_clause);
        let search_term = format!("%{}%", q);
        params_vec.push(Box::new(search_term.clone()));
        params_vec.push(Box::new(search_term.clone()));
        params_vec.push(Box::new(search_term));
    }

    if !filters.categories.is_empty() {
        let placeholders: Vec<&str> = filters.categories.iter().map(|_| "?").collect();
        let clause = format!(" AND category IN ({})", placeholders.join(","));
        query.push_str(&clause);
        count_query.push_str(&clause);
        for cat in &filters.categories {
            params_vec.push(Box::new(cat.clone()));
        }
    }

    if let Some(min) = filters.price_min {
        query.push_str(" AND price >= ?");
        count_query.push_str(" AND price >= ?");
        params_vec.push(Box::new(min));
    }

    if let Some(max) = filters.price_max {
        query.push_str(" AND price <= ?");
        count_query.push_str(" AND price <= ?");
        params_vec.push(Box::new(max));
    }

    if let Some(min) = filters.sales_min {
        query.push_str(" AND sales_count >= ?");
        count_query.push_str(" AND sales_count >= ?");
        params_vec.push(Box::new(min));
    }

    if let Some(min) = filters.rating_min {
        query.push_str(" AND product_rating >= ?");
        count_query.push_str(" AND product_rating >= ?");
        params_vec.push(Box::new(min));
    }

    if let Some(true) = filters.has_free_shipping {
        query.push_str(" AND has_free_shipping = 1");
        count_query.push_str(" AND has_free_shipping = 1");
    }

    if let Some(true) = filters.is_trending {
        query.push_str(" AND is_trending = 1");
        count_query.push_str(" AND is_trending = 1");
    }

    if let Some(true) = filters.is_on_sale {
        query.push_str(" AND is_on_sale = 1");
        count_query.push_str(" AND is_on_sale = 1");
    }

    // ORDER BY
    let sort_by = filters.sort_by.as_deref().unwrap_or("collected_at");
    let sort_order = filters.sort_order.as_deref().unwrap_or("DESC");
    query.push_str(&format!(" ORDER BY {} {}", sort_by, sort_order));

    // PAGINATION
    let page = filters.page.unwrap_or(1);
    let page_size = filters.page_size.unwrap_or(20);
    let offset = (page - 1) * page_size;
    query.push_str(&format!(" LIMIT {} OFFSET {}", page_size, offset));

    // Convert params to references for rusqlite
    let params_refs: Vec<&dyn rusqlite::ToSql> = params_vec.iter().map(|p| p.as_ref()).collect();

    // Execute count query
    let total: i64 = conn
        .query_row(&count_query, params_refs.as_slice(), |row| row.get(0))
        .unwrap_or(0);

    // Execute main query
    let mut stmt = conn.prepare(&query)?;
    let products = stmt
        .query_map(params_refs.as_slice(), |row| {
            Ok(Product {
                id: row.get(0)?,
                tiktok_id: row.get(1)?,
                title: row.get(2)?,
                description: row.get(3)?,
                price: row.get(4)?,
                original_price: row.get(5)?,
                currency: row
                    .get::<_, Option<String>>(6)?
                    .unwrap_or_else(|| "BRL".to_string()),
                category: row.get(7)?,
                subcategory: row.get(8)?,
                seller_name: row.get(9)?,
                seller_rating: row.get(10)?,
                product_rating: row.get(11)?,
                reviews_count: row.get(12)?,
                sales_count: row.get(13)?,
                sales_7d: row.get(14)?,
                sales_30d: row.get(15)?,
                commission_rate: row.get(16)?,
                image_url: row.get(17)?,
                images: serde_json::from_str(
                    &row.get::<_, Option<String>>(18)?
                        .unwrap_or_else(|| "[]".to_string()),
                )
                .unwrap_or_default(),
                video_url: row.get(19)?,
                product_url: row.get(20)?,
                affiliate_url: row.get(21)?,
                has_free_shipping: row.get::<_, i32>(22)? == 1,
                is_trending: row.get::<_, i32>(23)? == 1,
                is_on_sale: row.get::<_, i32>(24)? == 1,
                in_stock: row.get::<_, i32>(25)? == 1,
                stock_level: row.get(28).ok(), // Try to get stock_level, default to None if column missing or null
                collected_at: row.get(26)?,
                updated_at: row.get(27)?,
            })
        })?
        .filter_map(|r| r.ok())
        .collect::<Vec<_>>();

    let has_more = (page * page_size) < total as i32;

    Ok(PaginatedResponse {
        data: products,
        total,
        page,
        page_size,
        has_more,
    })
}

pub fn get_product_by_id(db_path: &Path, id: &str) -> Result<Option<Product>> {
    let conn = get_connection(db_path)?;

    let mut stmt = conn.prepare("SELECT * FROM products WHERE id = ?")?;
    let product = stmt
        .query_row(params![id], |row| {
            Ok(Product {
                id: row.get(0)?,
                tiktok_id: row.get(1)?,
                title: row.get(2)?,
                description: row.get(3)?,
                price: row.get(4)?,
                original_price: row.get(5)?,
                currency: row
                    .get::<_, Option<String>>(6)?
                    .unwrap_or_else(|| "BRL".to_string()),
                category: row.get(7)?,
                subcategory: row.get(8)?,
                seller_name: row.get(9)?,
                seller_rating: row.get(10)?,
                product_rating: row.get(11)?,
                reviews_count: row.get(12)?,
                sales_count: row.get(13)?,
                sales_7d: row.get(14)?,
                sales_30d: row.get(15)?,
                commission_rate: row.get(16)?,
                image_url: row.get(17)?,
                images: serde_json::from_str(
                    &row.get::<_, Option<String>>(18)?
                        .unwrap_or_else(|| "[]".to_string()),
                )
                .unwrap_or_default(),
                video_url: row.get(19)?,
                product_url: row.get(20)?,
                affiliate_url: row.get(21)?,
                has_free_shipping: row.get::<_, i32>(22)? == 1,
                is_trending: row.get::<_, i32>(23)? == 1,
                is_on_sale: row.get::<_, i32>(24)? == 1,
                in_stock: row.get::<_, i32>(25)? == 1,
                stock_level: row.get(28).ok(),
                collected_at: row.get(26)?,
                updated_at: row.get(27)?,
            })
        })
        .optional()?;

    Ok(product)
}

pub fn save_product_history(db_path: &Path, product: &Product) -> Result<()> {
    let conn = get_connection(db_path)?;
    let id = Uuid::new_v4().to_string();

    conn.execute(
        "INSERT INTO product_history (id, product_id, price, sales_count, stock_level, collected_at)
         VALUES (?, ?, ?, ?, ?, ?)",
        params![
            id,
            product.id,
            product.price,
            product.sales_count,
            product.stock_level,
            product.collected_at
        ],
    )?;
    Ok(())
}

pub fn save_product(db_path: &Path, product: &Product) -> Result<()> {
    let conn = get_connection(db_path)?;

    conn.execute(
        "INSERT OR REPLACE INTO products (
            id, tiktok_id, title, description, price, original_price, currency,
            category, subcategory, seller_name, seller_rating, product_rating,
            reviews_count, sales_count, sales_7d, sales_30d, commission_rate,
            image_url, images, video_url, product_url, affiliate_url,
            has_free_shipping, is_trending, is_on_sale, in_stock, stock_level,
            collected_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        params![
            product.id,
            product.tiktok_id,
            product.title,
            product.description,
            product.price,
            product.original_price,
            product.currency,
            product.category,
            product.subcategory,
            product.seller_name,
            product.seller_rating,
            product.product_rating,
            product.reviews_count,
            product.sales_count,
            product.sales_7d,
            product.sales_30d,
            product.commission_rate,
            product.image_url,
            serde_json::to_string(&product.images).unwrap_or_else(|_| "[]".to_string()),
            product.video_url,
            product.product_url,
            product.affiliate_url,
            product.has_free_shipping as i32,
            product.is_trending as i32,
            product.is_on_sale as i32,
            product.in_stock as i32,
            product.stock_level,
            product.collected_at,
            product.updated_at
        ],
    )?;

    // Save history
    let _ = save_product_history(db_path, product);

    Ok(())
}

// ==========================================
// FAVORITES QUERIES
// ==========================================

pub fn add_favorite(
    db_path: &Path,
    user_id: &str,
    product_id: &str,
    list_id: Option<&str>,
    notes: Option<&str>,
) -> Result<FavoriteItem> {
    let conn = get_connection(db_path)?;

    let id = Uuid::new_v4().to_string();
    let now = chrono::Utc::now().to_rfc3339();

    conn.execute(
        "INSERT INTO favorites (id, user_id, product_id, list_id, notes, added_at)
         VALUES (?, ?, ?, ?, ?, ?)",
        params![id, user_id, product_id, list_id, notes, now],
    )?;

    Ok(FavoriteItem {
        id,
        user_id: user_id.to_string(),
        product_id: product_id.to_string(),
        list_id: list_id.map(|s| s.to_string()),
        notes: notes.map(|s| s.to_string()),
        added_at: now,
    })
}

pub fn remove_favorite(db_path: &Path, user_id: &str, product_id: &str) -> Result<bool> {
    let conn = get_connection(db_path)?;

    let rows = conn.execute(
        "DELETE FROM favorites WHERE user_id = ? AND product_id = ?",
        params![user_id, product_id],
    )?;

    Ok(rows > 0)
}

pub fn get_favorites(
    db_path: &Path,
    user_id: &str,
    list_id: Option<&str>,
) -> Result<Vec<FavoriteWithProduct>> {
    let conn = get_connection(db_path)?;

    let mut query = String::from(
        "SELECT f.*, p.* FROM favorites f
         JOIN products p ON f.product_id = p.id
         WHERE f.user_id = ?",
    );

    if list_id.is_some() {
        query.push_str(" AND f.list_id = ?");
    }

    query.push_str(" ORDER BY f.added_at DESC");

    let mut stmt = conn.prepare(&query)?;

    let results = if let Some(lid) = list_id {
        stmt.query_map(params![user_id, lid], map_favorite_with_product)?
    } else {
        stmt.query_map(params![user_id], map_favorite_with_product)?
    };

    Ok(results.filter_map(|r| r.ok()).collect())
}

fn map_favorite_with_product(row: &rusqlite::Row) -> rusqlite::Result<FavoriteWithProduct> {
    Ok(FavoriteWithProduct {
        favorite: FavoriteItem {
            id: row.get(0)?,
            user_id: row.get(1)?,
            product_id: row.get(2)?,
            list_id: row.get(3)?,
            notes: row.get(4)?,
            added_at: row.get(5)?,
        },
        product: Product {
            id: row.get(6)?,
            tiktok_id: row.get(7)?,
            title: row.get(8)?,
            description: row.get(9)?,
            price: row.get(10)?,
            original_price: row.get(11)?,
            currency: row
                .get::<_, Option<String>>(12)?
                .unwrap_or_else(|| "BRL".to_string()),
            category: row.get(13)?,
            subcategory: row.get(14)?,
            seller_name: row.get(15)?,
            seller_rating: row.get(16)?,
            product_rating: row.get(17)?,
            reviews_count: row.get(18)?,
            sales_count: row.get(19)?,
            sales_7d: row.get(20)?,
            sales_30d: row.get(21)?,
            commission_rate: row.get(22)?,
            image_url: row.get(23)?,
            images: vec![],
            video_url: row.get(25)?,
            product_url: row.get(26)?,
            affiliate_url: row.get(27)?,
            has_free_shipping: row.get::<_, i32>(28)? == 1,
            is_trending: row.get::<_, i32>(29)? == 1,
            is_on_sale: row.get::<_, i32>(30)? == 1,
            in_stock: row.get::<_, i32>(31)? == 1,
            stock_level: row.get(34).ok(),
            collected_at: row.get(32)?,
            updated_at: row.get(33)?,
        },
    })
}

pub fn create_favorite_list(
    db_path: &Path,
    user_id: &str,
    name: &str,
    description: Option<&str>,
    color: Option<&str>,
    icon: Option<&str>,
) -> Result<FavoriteList> {
    let conn = get_connection(db_path)?;

    let id = Uuid::new_v4().to_string();
    let now = chrono::Utc::now().to_rfc3339();
    let color = color.unwrap_or("#FF0050");
    let icon = icon.unwrap_or("heart");

    conn.execute(
        "INSERT INTO favorite_lists (id, user_id, name, description, color, icon, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        params![id, user_id, name, description, color, icon, now, now],
    )?;

    Ok(FavoriteList {
        id,
        user_id: user_id.to_string(),
        name: name.to_string(),
        description: description.map(|s| s.to_string()),
        color: color.to_string(),
        icon: icon.to_string(),
        product_count: 0,
        created_at: now.clone(),
        updated_at: now,
    })
}

pub fn get_favorite_lists(db_path: &Path, user_id: &str) -> Result<Vec<FavoriteList>> {
    let conn = get_connection(db_path)?;

    let mut stmt = conn.prepare(
        "SELECT fl.*, COUNT(f.id) as product_count
         FROM favorite_lists fl
         LEFT JOIN favorites f ON f.list_id = fl.id
         WHERE fl.user_id = ?
         GROUP BY fl.id
         ORDER BY fl.created_at DESC",
    )?;

    let lists = stmt
        .query_map(params![user_id], |row| {
            Ok(FavoriteList {
                id: row.get(0)?,
                user_id: row.get(1)?,
                name: row.get(2)?,
                description: row.get(3)?,
                color: row.get(4)?,
                icon: row.get(5)?,
                created_at: row.get(6)?,
                updated_at: row.get(7)?,
                product_count: row.get(8)?,
            })
        })?
        .filter_map(|r| r.ok())
        .collect();

    Ok(lists)
}

pub fn delete_favorite_list(db_path: &Path, list_id: &str) -> Result<bool> {
    let conn = get_connection(db_path)?;

    // First, remove all items from the list
    conn.execute("DELETE FROM favorites WHERE list_id = ?", params![list_id])?;

    // Then delete the list
    let rows = conn.execute("DELETE FROM favorite_lists WHERE id = ?", params![list_id])?;

    Ok(rows > 0)
}

// ==========================================
// COPY HISTORY QUERIES
// ==========================================

pub fn save_copy_history(
    db_path: &Path,
    user_id: &str,
    product_id: Option<&str>,
    copy_type: &str,
    tone: &str,
    content: &str,
    tokens_used: i32,
) -> Result<()> {
    let conn = get_connection(db_path)?;

    let id = Uuid::new_v4().to_string();
    let now = chrono::Utc::now().to_rfc3339();

    conn.execute(
        "INSERT INTO copy_history (id, user_id, product_id, copy_type, tone, content, tokens_used, created_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        params![id, user_id, product_id, copy_type, tone, content, tokens_used, now],
    )?;

    Ok(())
}

pub fn get_copy_history(db_path: &Path, user_id: &str, limit: i32) -> Result<Vec<CopyHistory>> {
    let conn = get_connection(db_path)?;

    let mut stmt = conn
        .prepare("SELECT * FROM copy_history WHERE user_id = ? ORDER BY created_at DESC LIMIT ?")?;

    let history = stmt
        .query_map(params![user_id, limit], |row| {
            Ok(CopyHistory {
                id: row.get(0)?,
                user_id: row.get(1)?,
                product_id: row.get(2)?,
                copy_type: row.get(3)?,
                tone: row.get(4)?,
                content: row.get(5)?,
                tokens_used: row.get(6)?,
                is_favorite: row.get::<_, i32>(7)? == 1,
                created_at: row.get(8)?,
            })
        })?
        .filter_map(|r| r.ok())
        .collect();

    Ok(history)
}

// ==========================================
// SEARCH HISTORY QUERIES
// ==========================================

pub fn save_search_history(
    db_path: &Path,
    user_id: &str,
    query: &str,
    filters: &str,
    results_count: i32,
) -> Result<bool> {
    let conn = get_connection(db_path)?;

    let id = Uuid::new_v4().to_string();
    let now = chrono::Utc::now().to_rfc3339();

    conn.execute(
        "INSERT INTO search_history (id, user_id, query, filters, results_count, searched_at)
         VALUES (?, ?, ?, ?, ?, ?)",
        params![id, user_id, query, filters, results_count, now],
    )?;

    Ok(true)
}

pub fn get_search_history(
    db_path: &Path,
    user_id: &str,
    limit: i32,
) -> Result<Vec<SearchHistoryItem>> {
    let conn = get_connection(db_path)?;

    let mut stmt = conn.prepare(
        "SELECT * FROM search_history WHERE user_id = ? ORDER BY searched_at DESC LIMIT ?",
    )?;

    let history = stmt
        .query_map(params![user_id, limit], |row| {
            Ok(SearchHistoryItem {
                id: row.get(0)?,
                user_id: row.get(1)?,
                query: row.get(2)?,
                filters: row.get(3)?,
                results_count: row.get(4)?,
                searched_at: row.get(5)?,
            })
        })?
        .filter_map(|r| r.ok())
        .collect();

    Ok(history)
}

// ==========================================
// DASHBOARD STATS
// ==========================================

pub fn get_dashboard_stats(db_path: &Path, user_id: &str) -> Result<DashboardStats> {
    let conn = get_connection(db_path)?;

    let total_products: i64 = conn
        .query_row("SELECT COUNT(*) FROM products", [], |row| row.get(0))
        .unwrap_or(0);

    let trending_products: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM products WHERE is_trending = 1",
            [],
            |row| row.get(0),
        )
        .unwrap_or(0);

    let favorite_count: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM favorites WHERE user_id = ?",
            params![user_id],
            |row| row.get(0),
        )
        .unwrap_or(0);

    let today = chrono::Utc::now().format("%Y-%m-%d").to_string();
    let searches_today: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM search_history WHERE user_id = ? AND date(searched_at) = ?",
            params![user_id, today],
            |row| row.get(0),
        )
        .unwrap_or(0);

    let copies_generated: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM copy_history WHERE user_id = ?",
            params![user_id],
            |row| row.get(0),
        )
        .unwrap_or(0);

    // Get top categories
    let mut stmt = conn.prepare(
        "SELECT category, COUNT(*) as count FROM products 
         WHERE category IS NOT NULL 
         GROUP BY category 
         ORDER BY count DESC 
         LIMIT 5",
    )?;

    let top_categories: Vec<CategoryCount> = stmt
        .query_map([], |row| {
            Ok(CategoryCount {
                name: row.get(0)?,
                count: row.get(1)?,
            })
        })?
        .filter_map(|r| r.ok())
        .collect();

    Ok(DashboardStats {
        total_products,
        trending_products,
        favorite_count,
        searches_today,
        copies_generated,
        top_categories,
    })
}

pub fn save_error_page(db_path: &Path, url: &str, html: &str) -> Result<()> {
    let conn = Connection::open(db_path)?;
    conn.execute(
        "INSERT INTO error_pages (url, html) VALUES (?1, ?2)",
        params![url, html],
    )?;
    Ok(())
}

pub fn get_product_history(db_path: &Path, product_id: &str) -> Result<Vec<ProductHistory>> {
    let conn = get_connection(db_path)?;

    let mut stmt = conn.prepare(
        "SELECT id, product_id, price, sales_count, stock_level, collected_at 
         FROM product_history 
         WHERE product_id = ? 
         ORDER BY collected_at ASC",
    )?;

    let history = stmt
        .query_map(params![product_id], |row| {
            Ok(ProductHistory {
                id: row.get(0)?,
                product_id: row.get(1)?,
                price: row.get(2)?,
                sales_count: row.get(3)?,
                stock_level: row.get(4).ok(),
                collected_at: row.get(5)?,
            })
        })?
        .filter_map(|r| r.ok())
        .collect();

    Ok(history)
}

// ==================================================
// SUBSCRIPTION CACHE (SaaS Híbrido)
// ==================================================

use crate::models::CachedSubscription;

/// Initialize subscription cache table
pub fn init_subscription_tables(db_path: &Path) -> Result<()> {
    let conn = Connection::open(db_path)?;

    conn.execute_batch(
        "
        -- Subscription cache table
        CREATE TABLE IF NOT EXISTS subscription_cache (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            subscription_json TEXT NOT NULL,
            cached_at TEXT NOT NULL,
            valid_until TEXT NOT NULL,
            last_sync TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        -- Usage tracking table (for offline usage tracking)
        CREATE TABLE IF NOT EXISTS usage_tracking (
            id TEXT PRIMARY KEY,
            feature TEXT NOT NULL,
            used INTEGER DEFAULT 0,
            limit_value INTEGER DEFAULT 0,
            period_start TEXT NOT NULL,
            period_end TEXT NOT NULL,
            synced_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        -- Pending sync table (for hybrid mode)
        CREATE TABLE IF NOT EXISTS pending_sync (
            id TEXT PRIMARY KEY,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            operation TEXT NOT NULL,
            data_json TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            retry_count INTEGER DEFAULT 0,
            last_error TEXT
        );

        -- Indexes
        CREATE INDEX IF NOT EXISTS idx_usage_tracking_feature ON usage_tracking(feature);
        CREATE INDEX IF NOT EXISTS idx_pending_sync_entity ON pending_sync(entity_type, entity_id);
        ",
    )?;

    log::info!("Subscription tables initialized at {:?}", db_path);
    Ok(())
}

/// Save subscription cache to database
pub fn save_subscription_cache(db_path: &Path, cached: &CachedSubscription) -> Result<()> {
    let conn = Connection::open(db_path)?;
    
    // Ensure tables exist
    init_subscription_tables(db_path)?;
    
    let subscription_json = serde_json::to_string(&cached.subscription)
        .map_err(|e| rusqlite::Error::ToSqlConversionFailure(Box::new(e)))?;

    conn.execute(
        "INSERT OR REPLACE INTO subscription_cache 
         (id, subscription_json, cached_at, valid_until, last_sync, updated_at)
         VALUES (1, ?1, ?2, ?3, ?4, datetime('now'))",
        params![
            subscription_json,
            cached.cached_at,
            cached.valid_until,
            cached.last_sync,
        ],
    )?;

    Ok(())
}

/// Get subscription cache from database
pub fn get_subscription_cache(db_path: &Path) -> Result<Option<CachedSubscription>> {
    let conn = Connection::open(db_path)?;
    
    // Ensure tables exist
    let _ = init_subscription_tables(db_path);

    let result: Option<(String, String, String, String)> = conn
        .query_row(
            "SELECT subscription_json, cached_at, valid_until, last_sync 
             FROM subscription_cache WHERE id = 1",
            [],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?)),
        )
        .optional()?;

    match result {
        Some((json, cached_at, valid_until, last_sync)) => {
            let subscription = serde_json::from_str(&json)
                .map_err(|e| rusqlite::Error::ToSqlConversionFailure(Box::new(e)))?;
            
            Ok(Some(CachedSubscription {
                subscription,
                cached_at,
                valid_until,
                last_sync,
            }))
        }
        None => Ok(None),
    }
}

/// Update usage tracking for a feature
pub fn update_usage_tracking(
    db_path: &Path,
    feature: &str,
    increment: i32,
    limit: i32,
    period_start: &str,
    period_end: &str,
) -> Result<i32> {
    let conn = Connection::open(db_path)?;
    
    // Ensure tables exist
    let _ = init_subscription_tables(db_path);
    
    // Get current usage
    let current: i32 = conn
        .query_row(
            "SELECT used FROM usage_tracking WHERE feature = ? AND period_end > datetime('now')",
            params![feature],
            |row| row.get(0),
        )
        .unwrap_or(0);
    
    let new_usage = current + increment;
    
    // Insert or update
    conn.execute(
        "INSERT INTO usage_tracking (id, feature, used, limit_value, period_start, period_end, updated_at)
         VALUES (?1, ?2, ?3, ?4, ?5, ?6, datetime('now'))
         ON CONFLICT(id) DO UPDATE SET 
            used = ?3,
            updated_at = datetime('now')",
        params![
            format!("{}_{}", feature, period_start),
            feature,
            new_usage,
            limit,
            period_start,
            period_end,
        ],
    )?;
    
    Ok(new_usage)
}

/// Get usage for a feature
pub fn get_feature_usage(db_path: &Path, feature: &str) -> Result<(i32, i32)> {
    let conn = Connection::open(db_path)?;
    
    let result: Option<(i32, i32)> = conn
        .query_row(
            "SELECT used, limit_value FROM usage_tracking 
             WHERE feature = ? AND period_end > datetime('now')
             ORDER BY period_start DESC LIMIT 1",
            params![feature],
            |row| Ok((row.get(0)?, row.get(1)?)),
        )
        .optional()?;
    
    Ok(result.unwrap_or((0, 0)))
}

/// Add pending sync item (for hybrid mode)
pub fn add_pending_sync(
    db_path: &Path,
    entity_type: &str,
    entity_id: &str,
    operation: &str,
    data: Option<&str>,
) -> Result<String> {
    let conn = Connection::open(db_path)?;
    let id = Uuid::new_v4().to_string();
    
    conn.execute(
        "INSERT INTO pending_sync (id, entity_type, entity_id, operation, data_json)
         VALUES (?1, ?2, ?3, ?4, ?5)",
        params![id, entity_type, entity_id, operation, data],
    )?;
    
    Ok(id)
}

/// Get all pending sync items
pub fn get_pending_sync(db_path: &Path) -> Result<Vec<(String, String, String, String, Option<String>)>> {
    let conn = Connection::open(db_path)?;
    
    let mut stmt = conn.prepare(
        "SELECT id, entity_type, entity_id, operation, data_json 
         FROM pending_sync 
         ORDER BY created_at ASC"
    )?;
    
    let items = stmt
        .query_map([], |row| {
            Ok((
                row.get(0)?,
                row.get(1)?,
                row.get(2)?,
                row.get(3)?,
                row.get(4).ok(),
            ))
        })?
        .filter_map(|r| r.ok())
        .collect();
    
    Ok(items)
}

/// Remove pending sync item after successful sync
pub fn remove_pending_sync(db_path: &Path, id: &str) -> Result<()> {
    let conn = Connection::open(db_path)?;
    conn.execute("DELETE FROM pending_sync WHERE id = ?", params![id])?;
    Ok(())
}

/// Clear all subscription cache
pub fn clear_subscription_cache(db_path: &Path) -> Result<()> {
    let conn = Connection::open(db_path)?;
    conn.execute("DELETE FROM subscription_cache", [])?;
    conn.execute("DELETE FROM usage_tracking", [])?;
    Ok(())
}
