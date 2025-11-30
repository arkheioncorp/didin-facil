import axios from "axios";
import { User, License, Credits } from "@/types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_at: string;
  user: User;
  license?: License;
  credits?: Credits;
}

/**
 * Get auth token from localStorage
 */
export function getAuthToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("auth_token");
}

/**
 * Set auth token in localStorage
 */
export function setAuthToken(token: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem("auth_token", token);
}

/**
 * Clear auth token from localStorage
 */
export function clearAuthToken(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem("auth_token");
}

export const authService = {
  async login(email: string, password: string, hwid: string) {
    const response = await api.post<LoginResponse>("/auth/login", {
      email,
      password,
      hwid,
    });
    return response.data;
  },

  async register(email: string, password: string, name: string) {
    const response = await api.post("/auth/register", {
      email,
      password,
      name,
    });
    return response.data;
  },
  
  async verifyEmail(token: string) {
    const response = await api.get(`/auth/verify-email?token=${token}`);
    return response.data;
  },
  
  async forgotPassword(email: string) {
    const response = await api.post("/auth/forgot-password", { email });
    return response.data;
  },
  
  async resetPassword(token: string, newPassword: string, confirmPassword: string) {
    const response = await api.post("/auth/reset-password", {
      token,
      new_password: newPassword,
      confirm_password: confirmPassword
    });
    return response.data;
  }
};
