import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { User, License, Credits } from "@/types";

// Default values for new users
const DEFAULT_LICENSE: License = {
  id: null,
  isValid: false,
  isLifetime: false,
  plan: 'free',
  activatedAt: null,
  expiresAt: null,
  maxDevices: 1,
  activeDevices: 0,
  currentDeviceId: null,
  isCurrentDeviceAuthorized: false,
};

const DEFAULT_CREDITS: Credits = {
  balance: 10, // Trial credits
  totalPurchased: 0,
  totalUsed: 0,
  lastPurchaseAt: null,
  bonusBalance: 0,
  bonusExpiresAt: null,
};

interface UserStoreState {
  // User data
  user: User | null;
  license: License | null;
  credits: Credits | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  hasHydrated: boolean;
  
  // Theme
  theme: "light" | "dark" | "system";
  
  // Actions
  setUser: (user: User | null) => void;
  setLicense: (license: License | null) => void;
  setCredits: (credits: Credits | null) => void;
  setTheme: (theme: "light" | "dark" | "system") => void;
  setLoading: (loading: boolean) => void;
  
  // Auth actions
  login: (user: User, license?: License, credits?: Credits) => void;
  logout: () => void;
  
  // Update actions
  updateUser: (updates: Partial<User>) => void;
  updateCredits: (updates: Partial<Credits>) => void;
  updateLicense: (updates: Partial<License>) => void;
  
  // Credit actions
  useCredits: (amount: number) => boolean;
  addCredits: (amount: number, isBonus?: boolean) => void;
  
  // Hydration
  setHasHydrated: (state: boolean) => void;
}

export const useUserStore = create<UserStoreState>()(
  persist(
    (set, get) => ({
      user: null,
      license: null,
      credits: null,
      isAuthenticated: false,
      isLoading: false,
      hasHydrated: false,
      theme: "system",
      
      setUser: (user: User | null) =>
        set({ user, isAuthenticated: !!user }),
        
      setLicense: (license: License | null) =>
        set({ license }),

      setCredits: (credits: Credits | null) =>
        set({ credits }),
        
      setTheme: (theme: "light" | "dark" | "system") =>
        set({ theme }),

      setLoading: (loading: boolean) =>
        set({ isLoading: loading }),
        
      login: (user: User, license?: License, credits?: Credits) =>
        set({ 
          user, 
          license: license || DEFAULT_LICENSE,
          credits: credits || DEFAULT_CREDITS,
          isAuthenticated: true,
          isLoading: false,
        }),
        
      logout: () => {
        // Clear auth token
        if (typeof window !== 'undefined') {
          localStorage.removeItem('auth_token');
          localStorage.removeItem('device_hwid');
        }
        set({ 
          user: null, 
          license: null, 
          credits: null, 
          isAuthenticated: false,
          isLoading: false,
        });
      },
        
      updateUser: (updates: Partial<User>) =>
        set((state) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),

      updateCredits: (updates: Partial<Credits>) =>
        set((state) => ({
          credits: state.credits ? { ...state.credits, ...updates } : null,
        })),

      updateLicense: (updates: Partial<License>) =>
        set((state) => ({
          license: state.license ? { ...state.license, ...updates } : null,
        })),

      useCredits: (amount: number) => {
        const state = get();
        if (!state.credits) return false;
        
        const totalAvailable = state.credits.balance + state.credits.bonusBalance;
        if (totalAvailable < amount) return false;
        
        // Use bonus credits first
        let remaining = amount;
        let newBonusBalance = state.credits.bonusBalance;
        let newBalance = state.credits.balance;
        
        if (newBonusBalance >= remaining) {
          newBonusBalance -= remaining;
          remaining = 0;
        } else {
          remaining -= newBonusBalance;
          newBonusBalance = 0;
          newBalance -= remaining;
        }
        
        set({
          credits: {
            ...state.credits,
            balance: newBalance,
            bonusBalance: newBonusBalance,
            totalUsed: state.credits.totalUsed + amount,
          }
        });
        
        return true;
      },

      addCredits: (amount: number, isBonus = false) =>
        set((state) => {
          if (!state.credits) return {};
          
          if (isBonus) {
            return {
              credits: {
                ...state.credits,
                bonusBalance: state.credits.bonusBalance + amount,
                bonusExpiresAt: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(), // 30 days
              }
            };
          }
          
          return {
            credits: {
              ...state.credits,
              balance: state.credits.balance + amount,
              totalPurchased: state.credits.totalPurchased + amount,
              lastPurchaseAt: new Date().toISOString(),
            }
          };
        }),
        
      setHasHydrated: (state: boolean) =>
        set({ hasHydrated: state }),
    }),
    {
      name: "didin-user-v2", // Updated storage key for new format
      storage: createJSONStorage(() => localStorage),
      partialize: (state: UserStoreState) => ({
        user: state.user,
        license: state.license,
        credits: state.credits,
        isAuthenticated: state.isAuthenticated,
        theme: state.theme,
      }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.setHasHydrated(true);
        }
      },
    }
  )
);
