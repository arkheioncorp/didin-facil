import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { User, License, Credits, Subscription, PlanInfo, UsageStats } from "@/types";

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

// Default subscription for FREE plan
const DEFAULT_SUBSCRIPTION: Subscription = {
  id: 'free',
  plan: 'free',
  status: 'active',
  billingCycle: 'monthly',
  executionMode: 'web_only',
  currentPeriodStart: new Date().toISOString(),
  currentPeriodEnd: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
  marketplaces: ['tiktok'],
  limits: {
    price_searches: 50,
    price_alerts: 5,
    favorites: 20,
    social_posts: 10,
    social_accounts: 1,
    whatsapp_instances: 1,
    whatsapp_messages: 100,
    chatbot_flows: 0,
    crm_leads: 0,
    api_calls: 0,
  },
  features: {
    analytics_basic: true,
    analytics_advanced: false,
    analytics_export: false,
    chatbot_ai: false,
    crm_automation: false,
    support_email: true,
    support_priority: false,
    support_phone: false,
    api_access: false,
    offline_mode: false,
    hybrid_sync: false,
  },
};

interface UserStoreState {
  // User data
  user: User | null;
  license: License | null; // LEGACY - mantido para compatibilidade
  credits: Credits | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  hasHydrated: boolean;
  
  // NEW: Subscription SaaS
  subscription: Subscription | null;
  planInfo: PlanInfo | null;
  usage: UsageStats[];
  subscriptionLoading: boolean;
  subscriptionError: string | null;
  
  // Theme
  theme: "light" | "dark" | "system";
  
  // Actions
  setUser: (user: User | null) => void;
  setLicense: (license: License | null) => void;
  setCredits: (credits: Credits | null) => void;
  setTheme: (theme: "light" | "dark" | "system") => void;
  setLoading: (loading: boolean) => void;
  
  // NEW: Subscription actions
  setSubscription: (subscription: Subscription | null) => void;
  setPlanInfo: (planInfo: PlanInfo | null) => void;
  setUsage: (usage: UsageStats[]) => void;
  setSubscriptionLoading: (loading: boolean) => void;
  setSubscriptionError: (error: string | null) => void;
  updateSubscription: (updates: Partial<Subscription>) => void;
  fetchSubscription: () => Promise<void>;
  
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
  
  // NEW: Feature access helpers
  canUseFeature: (feature: string) => boolean;
  getFeatureLimit: (feature: string) => number;
  getFeatureUsage: (feature: string) => number;
  hasMarketplace: (marketplace: string) => boolean;
  
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
      
      // NEW: Subscription state
      subscription: null,
      planInfo: null,
      usage: [],
      subscriptionLoading: false,
      subscriptionError: null,
      
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
      
      // NEW: Subscription actions
      setSubscription: (subscription: Subscription | null) =>
        set({ subscription: subscription || DEFAULT_SUBSCRIPTION }),
      
      setPlanInfo: (planInfo: PlanInfo | null) =>
        set({ planInfo }),
      
      setUsage: (usage: UsageStats[]) =>
        set({ usage }),
      
      setSubscriptionLoading: (loading: boolean) =>
        set({ subscriptionLoading: loading }),
      
      setSubscriptionError: (error: string | null) =>
        set({ subscriptionError: error }),
      
      updateSubscription: (updates: Partial<Subscription>) =>
        set((state) => ({
          subscription: state.subscription 
            ? { ...state.subscription, ...updates } 
            : null,
        })),

      fetchSubscription: async () => {
        const state = get();
        if (!state.isAuthenticated) return;
        
        set({ subscriptionLoading: true, subscriptionError: null });
        
        try {
          const token = localStorage.getItem('auth_token');
          const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
          
          const response = await fetch(`${apiUrl}/subscription/current`, {
             headers: {
               'Authorization': `Bearer ${token}`
             }
          });
          
          if (!response.ok) throw new Error('Failed to fetch subscription');
          
          const data = await response.json();
          set({ 
            subscription: data.subscription,
            planInfo: data.plan,
            usage: data.usage || []
          });
        } catch (error) {
          console.error('Subscription fetch error:', error);
          set({ subscriptionError: (error as Error).message });
        } finally {
          set({ subscriptionLoading: false });
        }
      },
        
      login: (user: User, license?: License, credits?: Credits) =>
        set({ 
          user, 
          license: license || DEFAULT_LICENSE,
          credits: credits || DEFAULT_CREDITS,
          subscription: DEFAULT_SUBSCRIPTION,
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
          subscription: null,
          planInfo: null,
          usage: [],
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
      
      // NEW: Feature access helpers
      canUseFeature: (feature: string) => {
        const state = get();
        const subscription = state.subscription || DEFAULT_SUBSCRIPTION;
        
        // Check boolean features
        if (feature in subscription.features) {
          return subscription.features[feature];
        }
        
        // Check metered features
        if (feature in subscription.limits) {
          const limit = subscription.limits[feature];
          if (limit === -1) return true; // Unlimited
          
          const usageItem = state.usage.find(u => u.feature === feature);
          const current = usageItem?.current ?? 0;
          return current < limit;
        }
        
        return false;
      },
      
      getFeatureLimit: (feature: string) => {
        const state = get();
        const subscription = state.subscription || DEFAULT_SUBSCRIPTION;
        return subscription.limits[feature] ?? 0;
      },
      
      getFeatureUsage: (feature: string) => {
        const state = get();
        const usageItem = state.usage.find(u => u.feature === feature);
        return usageItem?.current ?? 0;
      },
      
      hasMarketplace: (marketplace: string) => {
        const state = get();
        const subscription = state.subscription || DEFAULT_SUBSCRIPTION;
        return subscription.marketplaces.includes(marketplace as any);
      },
        
      setHasHydrated: (state: boolean) =>
        set({ hasHydrated: state }),
    }),
    {
      name: "didin-user-v3", // Updated storage key for subscription support
      storage: createJSONStorage(() => localStorage),
      partialize: (state: UserStoreState) => ({
        user: state.user,
        license: state.license,
        credits: state.credits,
        subscription: state.subscription,
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
