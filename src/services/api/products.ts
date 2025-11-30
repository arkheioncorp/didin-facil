/**
 * Products API Service
 * Integração com o backend para gerenciamento de produtos
 */

import type { Product, PaginatedResponse } from "@/types";

// API base URL
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001';

// Get auth token
const getAuthToken = (): string | null => {
  return localStorage.getItem('auth_token');
};

// Common headers
const getHeaders = (): HeadersInit => {
  const token = getAuthToken();
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  };
};

// API Response types matching backend
export interface ProductsApiResponse {
  products: BackendProduct[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
  cached: boolean;
  cache_expires_at?: string;
}

export interface BackendProduct {
  id: string;
  external_id?: string;
  title: string;
  description?: string;
  price?: number;
  original_price?: number;
  category?: string;
  shop_name?: string;
  shop_url?: string;
  product_url?: string;
  image_url?: string;
  images?: string[];
  sales_count: number;
  review_count: number;
  rating?: number;
  trending_score?: number;
  source?: string;
  status?: string;
  metadata?: Record<string, unknown>;
  last_scraped_at?: string;
  created_at?: string;
  updated_at?: string;
}

export interface ProductFilters {
  page?: number;
  per_page?: number;
  category?: string;
  min_price?: number;
  max_price?: number;
  min_sales?: number;
  min_rating?: number;
  sort_by?: 'sales_30d' | 'sales_7d' | 'price' | 'rating' | 'newest';
  sort_order?: 'asc' | 'desc';
  search?: string;
  is_trending?: boolean;
  has_video?: boolean;
}

export interface CategoryInfo {
  name: string;
  slug: string;
  count: number;
  icon?: string;
}

// Transform backend product to frontend format
const transformProduct = (p: BackendProduct): Product => ({
  id: p.id,
  tiktokId: p.external_id || p.id,
  title: p.title,
  description: p.description || '',
  price: p.price || 0,
  originalPrice: p.original_price || null,
  currency: 'BRL',
  category: p.category || 'Outros',
  subcategory: null,
  sellerName: p.shop_name || '',
  sellerRating: null,
  productRating: p.rating || null,
  reviewsCount: p.review_count || 0,
  salesCount: p.sales_count || 0,
  sales7d: 0, // Backend may not have this, default to 0
  sales30d: p.sales_count || 0,
  commissionRate: null,
  imageUrl: p.image_url || '',
  images: p.images || [],
  videoUrl: null,
  productUrl: p.product_url || '',
  affiliateUrl: null,
  hasFreeShipping: false,
  isTrending: (p.trending_score || 0) > 50,
  isOnSale: (p.original_price || 0) > (p.price || 0),
  inStock: p.status === 'active',
  stockLevel: null,
  collectedAt: p.last_scraped_at || p.created_at || new Date().toISOString(),
  updatedAt: p.updated_at || new Date().toISOString(),
});

/**
 * Fetch products with filters from backend API
 */
export async function fetchProducts(filters: ProductFilters = {}): Promise<PaginatedResponse<Product>> {
  const {
    page = 1,
    per_page = 20,
    category,
    min_price,
    max_price,
    min_sales,
    sort_by = 'sales_30d',
    sort_order = 'desc',
    search,
  } = filters;

  // Build query params
  const params = new URLSearchParams();
  params.append('page', String(page));
  params.append('per_page', String(per_page));
  params.append('sort_by', sort_by);
  params.append('sort_order', sort_order);
  
  if (category && category !== 'all') params.append('category', category);
  if (min_price !== undefined) params.append('min_price', String(min_price));
  if (max_price !== undefined) params.append('max_price', String(max_price));
  if (min_sales !== undefined) params.append('min_sales', String(min_sales));

  // Use search endpoint if search query provided
  const endpoint = search 
    ? `${API_BASE_URL}/products/search?q=${encodeURIComponent(search)}&${params.toString()}`
    : `${API_BASE_URL}/products?${params.toString()}`;

  try {
    const response = await fetch(endpoint, {
      method: 'GET',
      headers: getHeaders(),
    });

    if (!response.ok) {
      // If 401, clear token
      if (response.status === 401) {
        localStorage.removeItem('auth_token');
      }
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    const data: ProductsApiResponse = await response.json();

    return {
      data: data.products.map(transformProduct),
      total: data.total,
      page: data.page,
      pageSize: data.per_page,
      hasMore: data.has_more,
    };
  } catch (error) {
    console.error('Error fetching products:', error);
    throw error;
  }
}

/**
 * Fetch trending products
 */
export async function fetchTrendingProducts(
  page = 1,
  per_page = 20,
  category?: string
): Promise<PaginatedResponse<Product>> {
  const params = new URLSearchParams();
  params.append('page', String(page));
  params.append('per_page', String(per_page));
  if (category && category !== 'all') params.append('category', category);

  try {
    const response = await fetch(
      `${API_BASE_URL}/products/trending?${params.toString()}`,
      {
        method: 'GET',
        headers: getHeaders(),
      }
    );

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    const data: ProductsApiResponse = await response.json();

    return {
      data: data.products.map(transformProduct),
      total: data.total,
      page: data.page,
      pageSize: data.per_page,
      hasMore: data.has_more,
    };
  } catch (error) {
    console.error('Error fetching trending products:', error);
    throw error;
  }
}

/**
 * Fetch available categories
 */
export async function fetchCategories(): Promise<CategoryInfo[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/products/categories`, {
      method: 'GET',
      headers: getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    const data = await response.json();
    return data.categories || [];
  } catch (error) {
    console.error('Error fetching categories:', error);
    // Return default categories on error
    return [
      { name: 'Todas', slug: 'all', count: 0 },
      { name: 'Eletrônicos', slug: 'electronics', count: 0 },
      { name: 'Moda', slug: 'fashion', count: 0 },
      { name: 'Casa', slug: 'home', count: 0 },
      { name: 'Beleza', slug: 'beauty', count: 0 },
      { name: 'Esportes', slug: 'sports', count: 0 },
    ];
  }
}

/**
 * Get single product by ID
 */
export async function fetchProductById(id: string): Promise<Product | null> {
  try {
    const response = await fetch(`${API_BASE_URL}/products/${id}`, {
      method: 'GET',
      headers: getHeaders(),
    });

    if (!response.ok) {
      if (response.status === 404) return null;
      throw new Error(`API Error: ${response.status}`);
    }

    const data: BackendProduct = await response.json();
    return transformProduct(data);
  } catch (error) {
    console.error('Error fetching product:', error);
    return null;
  }
}

/**
 * Add product to favorites
 */
export async function addProductToFavorites(productId: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/favorites`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ product_id: productId }),
    });

    return response.ok;
  } catch (error) {
    console.error('Error adding to favorites:', error);
    return false;
  }
}

/**
 * Remove product from favorites
 */
export async function removeProductFromFavorites(productId: string): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/favorites/${productId}`, {
      method: 'DELETE',
      headers: getHeaders(),
    });

    return response.ok;
  } catch (error) {
    console.error('Error removing from favorites:', error);
    return false;
  }
}

/**
 * Export products to CSV/Excel and trigger download
 */
export async function exportProductsToFile(
  productIds: string[],
  format: 'csv' | 'xlsx' = 'csv'
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/products/export`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ product_ids: productIds, format }),
    });

    if (!response.ok) {
      throw new Error(`Export failed: ${response.status}`);
    }

    const blob = await response.blob();
    
    // Create download link
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `products_export_${new Date().toISOString().split('T')[0]}.${format}`;
    document.body.appendChild(link);
    link.click();
    
    // Cleanup
    setTimeout(() => {
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    }, 100);
  } catch (error) {
    console.error('Error exporting products:', error);
    throw error;
  }
}

/**
 * Get product statistics
 */
export async function fetchProductStats(): Promise<{
  total: number;
  trending: number;
  categories: Record<string, number>;
  avgPrice: number;
  totalSales: number;
}> {
  try {
    const response = await fetch(`${API_BASE_URL}/products/stats`, {
      method: 'GET',
      headers: getHeaders(),
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Error fetching stats:', error);
    return {
      total: 0,
      trending: 0,
      categories: {},
      avgPrice: 0,
      totalSales: 0,
    };
  }
}
