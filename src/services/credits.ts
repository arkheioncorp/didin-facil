/**
 * Credits Service
 * Handle credit purchases and balance management via API
 */

import { getAuthToken } from "./auth";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8001";

export interface CreditPackage {
  id: string;
  slug: string;
  name: string;
  credits: number;
  price_brl: number;
  price_per_credit: number;
  discount_percent: number;
  is_active: boolean;
  is_popular: boolean;
}

export interface CreditBalance {
  credits_balance: number;
  credits_purchased: number;
  credits_used: number;
  has_lifetime_license: boolean;
}

export interface CreditPurchase {
  purchase_id: string;
  package_id: string;
  credits: number;
  amount_brl: number;
  status: "pending" | "approved" | "rejected" | "cancelled";
  payment_method: string;
  qr_code?: string;
  qr_code_base64?: string;
  pix_copy_paste?: string;
  expires_at?: string;
  created_at: string;
}

export interface CreditUsage {
  id: string;
  operation_type: string;
  credits_used: number;
  description?: string;
  created_at: string;
}

export interface CreditHistory {
  purchases: CreditPurchase[];
  usage: CreditUsage[];
  total_purchased: number;
  total_used: number;
}

async function fetchWithAuth<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getAuthToken();
  
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  
  return response.json();
}

/**
 * Get available credit packages
 */
export async function getCreditPackages(): Promise<CreditPackage[]> {
  return fetchWithAuth<CreditPackage[]>("/credits/packages");
}

/**
 * Get user credit balance
 */
export async function getCreditBalance(): Promise<CreditBalance> {
  return fetchWithAuth<CreditBalance>("/credits/balance");
}

/**
 * Purchase credits package
 */
export async function purchaseCredits(
  packageSlug: string,
  paymentMethod: "pix" | "card" | "boleto" = "pix",
  cpf?: string,
  name?: string,
  email?: string
): Promise<CreditPurchase> {
  return fetchWithAuth<CreditPurchase>("/credits/purchase", {
    method: "POST",
    body: JSON.stringify({
      package_slug: packageSlug,
      payment_method: paymentMethod,
      cpf,
      name,
      email
    }),
  });
}

/**
 * Check purchase status
 */
export async function checkPurchaseStatus(
  purchaseId: string
): Promise<CreditPurchase> {
  return fetchWithAuth<CreditPurchase>(`/credits/purchase/${purchaseId}/status`);
}

/**
 * Get credit history (purchases and usage)
 */
export async function getCreditHistory(): Promise<CreditHistory> {
  return fetchWithAuth<CreditHistory>("/credits/history");
}

/**
 * Poll for payment status until approved or timeout
 */
export async function pollPaymentStatus(
  purchaseId: string,
  onStatusChange: (status: CreditPurchase) => void,
  timeoutMs: number = 300000, // 5 minutes
  intervalMs: number = 3000 // 3 seconds
): Promise<CreditPurchase> {
  const startTime = Date.now();
  
  return new Promise((resolve, reject) => {
    const poll = async () => {
      try {
        const status = await checkPurchaseStatus(purchaseId);
        onStatusChange(status);
        
        if (status.status === "approved") {
          resolve(status);
          return;
        }
        
        if (status.status === "rejected" || status.status === "cancelled") {
          reject(new Error(`Payment ${status.status}`));
          return;
        }
        
        // Check timeout
        if (Date.now() - startTime > timeoutMs) {
          reject(new Error("Payment timeout"));
          return;
        }
        
        // Continue polling
        setTimeout(poll, intervalMs);
      } catch (error) {
        reject(error);
      }
    };
    
    poll();
  });
}
