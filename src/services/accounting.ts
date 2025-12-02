/**
 * Admin Accounting Service
 * Financial dashboard and reporting APIs
 */

import { getAuthToken } from "./auth";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Backend response types (match backend models)
export interface DashboardMetrics {
  period_days: number;
  total_revenue: number;
  total_costs: number;
  openai_costs: number;
  gross_profit: number;
  profit_margin_percent: number;
  credits_sold: number;
  credits_consumed: number;
  transactions_count: number;
  avg_transaction_value: number;
}

export interface DailyRevenueItem {
  date: string;
  revenue: number;
  costs: number;
  profit: number;
  transactions: number;
}

export interface OperationsBreakdown {
  copy_generation: number;
  trend_analysis: number;
  niche_report: number;
  ai_chat: number;
  image_generation: number;
}

export interface TopUser {
  user_id: string;
  total_spent: number;
  credits_purchased: number;
  credits_used: number;
  purchase_count: number;
  lifetime_profit: number;
}

export interface PackageSales {
  name: string;
  slug: string;
  sales: number;
  revenue: number;
  credits: number;
}

export interface FinancialSummary {
  metrics: DashboardMetrics;
  revenue_by_day: DailyRevenueItem[];
  operations_breakdown: OperationsBreakdown;
  top_users: TopUser[];
  package_sales: PackageSales[];
}

// Legacy types for compatibility
export interface DailyMetrics {
  date: string;
  revenue_brl: number;
  cost_brl: number;
  profit_brl: number;
  profit_margin: number;
  total_operations: number;
  total_tokens: number;
  credit_purchases: number;
  credits_used: number;
  new_users: number;
  active_users: number;
}

export interface MonthlyMetrics {
  month: string;
  revenue_brl: number;
  cost_brl: number;
  profit_brl: number;
  profit_margin: number;
  total_operations: number;
  credit_purchases: number;
  new_users: number;
  mrr: number;
  arpu: number;
}

export interface GrowthMetrics {
  revenue_day_over_day: number;
  revenue_month_over_month: number;
  users_day_over_day: number;
  users_month_over_month: number;
}

export interface OperationCost {
  operation_type: string;
  credit_cost: number;
  avg_token_cost_usd: number;
  total_operations: number;
  total_revenue_brl: number;
  total_cost_brl: number;
  profit_margin: number;
}

export interface UserLTV {
  user_id: string;
  email: string;
  total_spent_brl: number;
  total_credits_purchased: number;
  total_credits_used: number;
  first_purchase_at: string;
  last_purchase_at: string;
  purchase_count: number;
  avg_purchase_value: number;
  lifetime_days: number;
  predicted_ltv: number;
}

export interface DailyReport {
  date: string;
  revenue_brl: number;
  cost_brl: number;
  profit_brl: number;
  profit_margin: number;
  operations: {
    copy: number;
    trend_analysis: number;
    niche_report: number;
  };
  top_users: Array<{
    email: string;
    operations: number;
    credits_used: number;
  }>;
}

async function fetchWithAuth<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...options.headers as Record<string, string>,
  };

  // Add token if available
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Authentication required");
    }
    if (response.status === 403) {
      throw new Error("Admin access required");
    }
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Get complete financial summary (recommended - single request)
 */
export async function getFinancialSummary(days: number = 30): Promise<FinancialSummary> {
  return fetchWithAuth<FinancialSummary>(`/admin/accounting/summary?days=${days}`);
}

/**
 * Get admin dashboard metrics
 */
export async function getAdminDashboard(days: number = 30): Promise<DashboardMetrics> {
  return fetchWithAuth<DashboardMetrics>(`/admin/accounting/dashboard?days=${days}`);
}

/**
 * Get daily revenue data for charts
 */
export async function getDailyRevenue(days: number = 30): Promise<DailyRevenueItem[]> {
  return fetchWithAuth<DailyRevenueItem[]>(`/admin/accounting/revenue/daily?days=${days}`);
}

/**
 * Get operations breakdown by type
 */
export async function getOperationsBreakdown(days: number = 30): Promise<OperationsBreakdown> {
  return fetchWithAuth<OperationsBreakdown>(`/admin/accounting/operations/breakdown?days=${days}`);
}

/**
 * Get top spending users
 */
export async function getTopUsers(limit: number = 10): Promise<TopUser[]> {
  return fetchWithAuth<TopUser[]>(`/admin/accounting/users/top?limit=${limit}`);
}

/**
 * Get package sales stats
 */
export async function getPackageSales(days: number = 30): Promise<PackageSales[]> {
  return fetchWithAuth<PackageSales[]>(`/admin/accounting/packages/sales?days=${days}`);
}

/**
 * Generate daily report manually
 */
export async function generateDailyReport(date?: Date): Promise<{ success: boolean; report_date: string }> {
  const query = date ? `?date=${date.toISOString()}` : "";
  return fetchWithAuth<{ success: boolean; report_date: string }>(`/admin/accounting/reports/generate-daily${query}`, {
    method: "POST",
  });
}

/**
 * Export financial report
 */
export async function exportFinancialReport(
  startDate: Date,
  endDate: Date,
  format: "csv" | "json" | "xlsx" = "csv"
): Promise<void> {
  const token = getAuthToken();
  if (!token) throw new Error("Authentication required");

  const query = new URLSearchParams({
    start_date: startDate.toISOString(),
    end_date: endDate.toISOString(),
    format,
  }).toString();

  const response = await fetch(`${API_URL}/admin/accounting/reports/export?${query}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to export report");
  }

  // Handle file download
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `financial_report_${format}.${format === "xlsx" ? "xlsx" : format}`; // Simple filename, backend sends content-disposition too
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

// Legacy functions for backward compatibility (deprecated)
export async function getDailyReports(
  startDate: string,
  endDate: string
): Promise<DailyReport[]> {
  console.warn("getDailyReports is deprecated, use getDailyRevenue instead");
  // Convert to new API format
  const data = await getDailyRevenue(30);
  return data.map(item => ({
    date: item.date,
    revenue_brl: item.revenue,
    cost_brl: item.costs,
    profit_brl: item.profit,
    profit_margin: item.revenue > 0 ? (item.profit / item.revenue) * 100 : 0,
    operations: { copy: 0, trend_analysis: 0, niche_report: 0 },
    top_users: [],
  }));
}

export async function getUsersLTV(limit: number = 50): Promise<UserLTV[]> {
  console.warn("getUsersLTV is deprecated, use getTopUsers instead");
  const users = await getTopUsers(limit);
  return users.map(u => ({
    user_id: u.user_id,
    email: "",
    total_spent_brl: u.total_spent,
    total_credits_purchased: u.credits_purchased,
    total_credits_used: u.credits_used,
    first_purchase_at: "",
    last_purchase_at: "",
    purchase_count: u.purchase_count,
    avg_purchase_value: u.total_spent / u.purchase_count,
    lifetime_days: 0,
    predicted_ltv: u.lifetime_profit,
  }));
}

export async function getOperationCosts(): Promise<OperationCost[]> {
  console.warn("getOperationCosts is deprecated");
  return [];
}

export async function getMonthlyReports(year: number): Promise<MonthlyMetrics[]> {
  console.warn("getMonthlyReports is deprecated");
  return [];
}

export async function updateOperationCost(
  operationType: string,
  creditCost: number
): Promise<{ success: boolean }> {
  console.warn("updateOperationCost is deprecated");
  return { success: false };
}
