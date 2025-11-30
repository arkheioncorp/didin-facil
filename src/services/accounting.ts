/**
 * Admin Accounting Service
 * Financial dashboard and reporting APIs
 */

import { getAuthToken } from "./auth";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8001";

export interface DashboardMetrics {
  today: DailyMetrics;
  yesterday: DailyMetrics;
  this_month: MonthlyMetrics;
  last_month: MonthlyMetrics;
  growth: GrowthMetrics;
}

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
  
  if (!token) {
    throw new Error("Authentication required");
  }
  
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...options.headers,
    },
  });
  
  if (!response.ok) {
    if (response.status === 403) {
      throw new Error("Admin access required");
    }
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * Get admin dashboard metrics
 */
export async function getAdminDashboard(): Promise<DashboardMetrics> {
  return fetchWithAuth<DashboardMetrics>("/accounting/admin/dashboard");
}

/**
 * Get daily reports for date range
 */
export async function getDailyReports(
  startDate: string,
  endDate: string
): Promise<DailyReport[]> {
  const params = new URLSearchParams({ start_date: startDate, end_date: endDate });
  return fetchWithAuth<DailyReport[]>(`/accounting/admin/reports/daily?${params}`);
}

/**
 * Get monthly reports
 */
export async function getMonthlyReports(
  year: number
): Promise<MonthlyMetrics[]> {
  return fetchWithAuth<MonthlyMetrics[]>(`/accounting/admin/reports/monthly?year=${year}`);
}

/**
 * Get user LTV analysis
 */
export async function getUsersLTV(
  limit: number = 50
): Promise<UserLTV[]> {
  return fetchWithAuth<UserLTV[]>(`/accounting/admin/users/ltv?limit=${limit}`);
}

/**
 * Get operation costs breakdown
 */
export async function getOperationCosts(): Promise<OperationCost[]> {
  return fetchWithAuth<OperationCost[]>("/accounting/admin/costs");
}

/**
 * Update operation cost settings
 */
export async function updateOperationCost(
  operationType: string,
  creditCost: number
): Promise<{ success: boolean }> {
  return fetchWithAuth<{ success: boolean }>("/accounting/admin/costs", {
    method: "PUT",
    body: JSON.stringify({
      operation_type: operationType,
      credit_cost: creditCost,
    }),
  });
}
