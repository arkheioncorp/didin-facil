import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

// ============================================
// TYPES
// ============================================

export interface ProductMetric {
  timestamp: string;
  value: number;
  source?: string;
}

export interface ProductAnalytics {
  productId: string;
  
  // Engagement metrics
  views: ProductMetric[];
  clicks: ProductMetric[];
  shares: ProductMetric[];
  saves: ProductMetric[];
  
  // Social media metrics
  instagramPosts: number;
  tiktokPosts: number;
  youtubePosts: number;
  whatsappShares: number;
  
  // Conversion metrics
  conversions: ProductMetric[];
  revenue: ProductMetric[];
  
  // Action metrics
  actionsExecuted: number;
  copiesGenerated: number;
  templatesUsed: number;
  
  // Timestamps
  firstSeen: string;
  lastActivity: string;
}

export interface AnalyticsState {
  analytics: Record<string, ProductAnalytics>;
  
  // Actions
  trackView: (productId: string, source?: string) => void;
  trackClick: (productId: string, source?: string) => void;
  trackShare: (productId: string, platform: string) => void;
  trackSave: (productId: string) => void;
  trackConversion: (productId: string, value: number) => void;
  trackSocialPost: (productId: string, platform: "instagram" | "tiktok" | "youtube" | "whatsapp") => void;
  trackActionExecuted: (productId: string) => void;
  trackCopyGenerated: (productId: string) => void;
  trackTemplateUsed: (productId: string) => void;
  
  // Getters
  getProductAnalytics: (productId: string) => ProductAnalytics | undefined;
  getTopProducts: (metric: "views" | "clicks" | "conversions", limit?: number) => Array<{ productId: string; total: number }>;
  getProductStats: (productId: string) => {
    totalViews: number;
    totalClicks: number;
    totalShares: number;
    totalConversions: number;
    totalRevenue: number;
    engagementRate: number;
    conversionRate: number;
  };
  getTrend: (productId: string, metric: "views" | "clicks" | "conversions", days?: number) => number;
  
  // Reset
  clearProductAnalytics: (productId: string) => void;
  clearAllAnalytics: () => void;
}

// ============================================
// HELPERS
// ============================================

const createEmptyAnalytics = (productId: string): ProductAnalytics => ({
  productId,
  views: [],
  clicks: [],
  shares: [],
  saves: [],
  instagramPosts: 0,
  tiktokPosts: 0,
  youtubePosts: 0,
  whatsappShares: 0,
  conversions: [],
  revenue: [],
  actionsExecuted: 0,
  copiesGenerated: 0,
  templatesUsed: 0,
  firstSeen: new Date().toISOString(),
  lastActivity: new Date().toISOString(),
});

const sumMetrics = (metrics: ProductMetric[], days?: number): number => {
  const cutoff = days 
    ? new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString()
    : undefined;
    
  return metrics
    .filter((m) => !cutoff || m.timestamp >= cutoff)
    .reduce((sum, m) => sum + m.value, 0);
};

// ============================================
// STORE
// ============================================

export const useProductAnalyticsStore = create<AnalyticsState>()(
  persist(
    (set, get) => ({
      analytics: {},

      trackView: (productId, source) => {
        const now = new Date().toISOString();
        set((state) => {
          const current = state.analytics[productId] || createEmptyAnalytics(productId);
          return {
            analytics: {
              ...state.analytics,
              [productId]: {
                ...current,
                views: [...current.views, { timestamp: now, value: 1, source }],
                lastActivity: now,
              },
            },
          };
        });
      },

      trackClick: (productId, source) => {
        const now = new Date().toISOString();
        set((state) => {
          const current = state.analytics[productId] || createEmptyAnalytics(productId);
          return {
            analytics: {
              ...state.analytics,
              [productId]: {
                ...current,
                clicks: [...current.clicks, { timestamp: now, value: 1, source }],
                lastActivity: now,
              },
            },
          };
        });
      },

      trackShare: (productId, platform) => {
        const now = new Date().toISOString();
        set((state) => {
          const current = state.analytics[productId] || createEmptyAnalytics(productId);
          return {
            analytics: {
              ...state.analytics,
              [productId]: {
                ...current,
                shares: [...current.shares, { timestamp: now, value: 1, source: platform }],
                lastActivity: now,
              },
            },
          };
        });
      },

      trackSave: (productId) => {
        const now = new Date().toISOString();
        set((state) => {
          const current = state.analytics[productId] || createEmptyAnalytics(productId);
          return {
            analytics: {
              ...state.analytics,
              [productId]: {
                ...current,
                saves: [...current.saves, { timestamp: now, value: 1 }],
                lastActivity: now,
              },
            },
          };
        });
      },

      trackConversion: (productId, value) => {
        const now = new Date().toISOString();
        set((state) => {
          const current = state.analytics[productId] || createEmptyAnalytics(productId);
          return {
            analytics: {
              ...state.analytics,
              [productId]: {
                ...current,
                conversions: [...current.conversions, { timestamp: now, value: 1 }],
                revenue: [...current.revenue, { timestamp: now, value }],
                lastActivity: now,
              },
            },
          };
        });
      },

      trackSocialPost: (productId, platform) => {
        const now = new Date().toISOString();
        set((state) => {
          const current = state.analytics[productId] || createEmptyAnalytics(productId);
          const updates: Partial<ProductAnalytics> = { lastActivity: now };
          
          switch (platform) {
            case "instagram":
              updates.instagramPosts = current.instagramPosts + 1;
              break;
            case "tiktok":
              updates.tiktokPosts = current.tiktokPosts + 1;
              break;
            case "youtube":
              updates.youtubePosts = current.youtubePosts + 1;
              break;
            case "whatsapp":
              updates.whatsappShares = current.whatsappShares + 1;
              break;
          }
          
          return {
            analytics: {
              ...state.analytics,
              [productId]: { ...current, ...updates },
            },
          };
        });
      },

      trackActionExecuted: (productId) => {
        const now = new Date().toISOString();
        set((state) => {
          const current = state.analytics[productId] || createEmptyAnalytics(productId);
          return {
            analytics: {
              ...state.analytics,
              [productId]: {
                ...current,
                actionsExecuted: current.actionsExecuted + 1,
                lastActivity: now,
              },
            },
          };
        });
      },

      trackCopyGenerated: (productId) => {
        const now = new Date().toISOString();
        set((state) => {
          const current = state.analytics[productId] || createEmptyAnalytics(productId);
          return {
            analytics: {
              ...state.analytics,
              [productId]: {
                ...current,
                copiesGenerated: current.copiesGenerated + 1,
                lastActivity: now,
              },
            },
          };
        });
      },

      trackTemplateUsed: (productId) => {
        const now = new Date().toISOString();
        set((state) => {
          const current = state.analytics[productId] || createEmptyAnalytics(productId);
          return {
            analytics: {
              ...state.analytics,
              [productId]: {
                ...current,
                templatesUsed: current.templatesUsed + 1,
                lastActivity: now,
              },
            },
          };
        });
      },

      getProductAnalytics: (productId) => {
        return get().analytics[productId];
      },

      getTopProducts: (metric, limit = 10) => {
        const analytics = get().analytics;
        const results: Array<{ productId: string; total: number }> = [];

        for (const [productId, data] of Object.entries(analytics)) {
          let total = 0;
          switch (metric) {
            case "views":
              total = sumMetrics(data.views);
              break;
            case "clicks":
              total = sumMetrics(data.clicks);
              break;
            case "conversions":
              total = sumMetrics(data.conversions);
              break;
          }
          results.push({ productId, total });
        }

        return results.sort((a, b) => b.total - a.total).slice(0, limit);
      },

      getProductStats: (productId) => {
        const data = get().analytics[productId];
        if (!data) {
          return {
            totalViews: 0,
            totalClicks: 0,
            totalShares: 0,
            totalConversions: 0,
            totalRevenue: 0,
            engagementRate: 0,
            conversionRate: 0,
          };
        }

        const totalViews = sumMetrics(data.views);
        const totalClicks = sumMetrics(data.clicks);
        const totalShares = sumMetrics(data.shares);
        const totalConversions = sumMetrics(data.conversions);
        const totalRevenue = sumMetrics(data.revenue);

        const engagementRate = totalViews > 0 
          ? ((totalClicks + totalShares) / totalViews) * 100 
          : 0;
        const conversionRate = totalClicks > 0 
          ? (totalConversions / totalClicks) * 100 
          : 0;

        return {
          totalViews,
          totalClicks,
          totalShares,
          totalConversions,
          totalRevenue,
          engagementRate: Math.round(engagementRate * 100) / 100,
          conversionRate: Math.round(conversionRate * 100) / 100,
        };
      },

      getTrend: (productId, metric, days = 7) => {
        const data = get().analytics[productId];
        if (!data) return 0;

        const now = Date.now();
        const currentPeriodStart = now - days * 24 * 60 * 60 * 1000;
        const previousPeriodStart = now - 2 * days * 24 * 60 * 60 * 1000;

        let metrics: ProductMetric[];
        switch (metric) {
          case "views":
            metrics = data.views;
            break;
          case "clicks":
            metrics = data.clicks;
            break;
          case "conversions":
            metrics = data.conversions;
            break;
        }

        const currentPeriod = metrics.filter((m) => {
          const time = new Date(m.timestamp).getTime();
          return time >= currentPeriodStart;
        });

        const previousPeriod = metrics.filter((m) => {
          const time = new Date(m.timestamp).getTime();
          return time >= previousPeriodStart && time < currentPeriodStart;
        });

        const currentTotal = currentPeriod.reduce((sum, m) => sum + m.value, 0);
        const previousTotal = previousPeriod.reduce((sum, m) => sum + m.value, 0);

        if (previousTotal === 0) return currentTotal > 0 ? 100 : 0;
        return Math.round(((currentTotal - previousTotal) / previousTotal) * 100);
      },

      clearProductAnalytics: (productId) => {
        set((state) => {
          const { [productId]: _, ...rest } = state.analytics;
          return { analytics: rest };
        });
      },

      clearAllAnalytics: () => {
        set({ analytics: {} });
      },
    }),
    {
      name: "product-analytics-storage",
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        // Limit stored data to prevent localStorage overflow
        analytics: Object.fromEntries(
          Object.entries(state.analytics).map(([id, data]) => [
            id,
            {
              ...data,
              // Keep only last 100 entries per metric
              views: data.views.slice(-100),
              clicks: data.clicks.slice(-100),
              shares: data.shares.slice(-100),
              saves: data.saves.slice(-100),
              conversions: data.conversions.slice(-100),
              revenue: data.revenue.slice(-100),
            },
          ])
        ),
      }),
    }
  )
);
