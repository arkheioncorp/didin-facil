import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { User, License, Credits } from "@/types";

interface UserState {
  // User data
  user: User | null;
  license: License | null;
  credits: Credits | null;
  isAuthenticated: boolean;
  hasHydrated: boolean;
  
  // Theme
  theme: "light" | "dark" | "system";
  
  // Actions
  setUser: (user: User | null) => void;
  setLicense: (license: License | null) => void;
  setCredits: (credits: Credits | null) => void;
  setTheme: (theme: "light" | "dark" | "system") => void;
  login: (user: User, license: License, credits?: Credits) => void;
  logout: () => void;
  updateUser: (updates: Partial<User>) => void;
  updateCredits: (balance: number) => void;
  setHasHydrated: (state: boolean) => void;
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      user: null,
      license: null,
      credits: null,
      isAuthenticated: false,
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
        
      login: (user: User, license: License, credits?: Credits) =>
        set({ 
          user, 
          license, 
          credits: credits || { balance: 0, totalPurchased: 0, totalUsed: 0, lastPurchaseAt: null },
          isAuthenticated: true 
        }),
        
      logout: () =>
        set({ user: null, license: null, credits: null, isAuthenticated: false }),
        
      updateUser: (updates: Partial<User>) =>
        set((state: UserState) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),

      updateCredits: (balance: number) =>
        set((state: UserState) => ({
          credits: state.credits ? { ...state.credits, balance } : null,
        })),
        
      setHasHydrated: (state: boolean) =>
        set({ hasHydrated: state }),
    }),
    {
      name: "tiktrend-user",
      storage: createJSONStorage(() => localStorage),
      partialize: (state: UserState) => ({
        user: state.user,
        license: state.license,
        credits: state.credits,
        isAuthenticated: state.isAuthenticated,
        theme: state.theme,
      }),
      onRehydrateStorage: () => (state) => {
        // Always set hasHydrated to true after rehydration, even if there's no data
        if (state) {
          state.setHasHydrated(true);
        }
      },
    }
  )
);

// Ensure hasHydrated is set even if persist middleware fails
// This handles the case where localStorage is empty
if (typeof window !== 'undefined') {
  setTimeout(() => {
    const state = useUserStore.getState();
    if (!state.hasHydrated) {
      useUserStore.setState({ hasHydrated: true });
    }
  }, 100);
}
