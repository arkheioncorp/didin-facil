/**
 * API Client for HTTP requests
 * Used for direct API calls (WhatsApp, Social, Scheduler, etc.)
 */

import { API_BASE_URL } from "./constants";

interface RequestConfig {
  headers?: Record<string, string>;
  params?: Record<string, string>;
}

interface ApiResponse<T> {
  data: T;
  status: number;
}

class ApiClient {
  private baseURL: string;
  private defaultHeaders: Record<string, string>;

  constructor(baseURL: string) {
    this.baseURL = baseURL;
    this.defaultHeaders = {
      "Content-Type": "application/json",
    };
  }

  private async request<T>(
    method: string,
    endpoint: string,
    data?: unknown,
    config?: RequestConfig
  ): Promise<ApiResponse<T>> {
    const url = new URL(endpoint, this.baseURL);
    
    // Add query params
    if (config?.params) {
      Object.entries(config.params).forEach(([key, value]) => {
        if (value !== undefined && value !== null) {
          url.searchParams.append(key, value);
        }
      });
    }

    const headers: Record<string, string> = {
      ...this.defaultHeaders,
      ...config?.headers,
    };

    // Get auth token from localStorage if available
    const token = localStorage.getItem("auth_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    // Handle FormData - don't set Content-Type, let browser set it with boundary
    const isFormData = data instanceof FormData;
    if (isFormData) {
      delete headers["Content-Type"];
    }

    const fetchConfig: RequestInit = {
      method,
      headers,
      body: data 
        ? isFormData 
          ? data as BodyInit
          : JSON.stringify(data) 
        : undefined,
    };

    try {
      const response = await fetch(url.toString(), fetchConfig);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || errorData.message || `HTTP ${response.status}`);
      }

      const responseData = await response.json();
      
      return {
        data: responseData,
        status: response.status,
      };
    } catch (error) {
      if (error instanceof Error) {
        throw error;
      }
      throw new Error("Network error");
    }
  }

  async get<T>(endpoint: string, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>("GET", endpoint, undefined, config);
  }

  async post<T>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>("POST", endpoint, data, config);
  }

  async put<T>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>("PUT", endpoint, data, config);
  }

  async delete<T>(endpoint: string, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>("DELETE", endpoint, undefined, config);
  }

  async patch<T>(endpoint: string, data?: unknown, config?: RequestConfig): Promise<ApiResponse<T>> {
    return this.request<T>("PATCH", endpoint, data, config);
  }

  setAuthToken(token: string) {
    localStorage.setItem("auth_token", token);
  }

  clearAuthToken() {
    localStorage.removeItem("auth_token");
  }
}

// Export singleton instance
export const api = new ApiClient(API_BASE_URL);
