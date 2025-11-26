import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type { User, License } from "@/types";

interface UserState {
  // User data
  user: User | null;
  license: License | null;
  isAuthenticated: boolean;
  
  // Theme
  theme: "light" | "dark" | "system";
  
  // Actions
  setUser: (user: User | null) => void;
  setLicense: (license: License | null) => void;
  setTheme: (theme: "light" | "dark" | "system") => void;
  login: (user: User, license: License) => void;
  logout: () => void;
  updateUser: (updates: Partial<User>) => void;
}

export const useUserStore = create<UserState>()(
  persist(
    (set) => ({
      user: null,
      license: null,
      isAuthenticated: false,
      theme: "system",
      
      setUser: (user: User | null) =>
        set({ user, isAuthenticated: !!user }),
        
      setLicense: (license: License | null) =>
        set({ license }),
        
      setTheme: (theme: "light" | "dark" | "system") =>
        set({ theme }),
        
      login: (user: User, license: License) =>
        set({ user, license, isAuthenticated: true }),
        
      logout: () =>
        set({ user: null, license: null, isAuthenticated: false }),
        
      updateUser: (updates: Partial<User>) =>
        set((state: UserState) => ({
          user: state.user ? { ...state.user, ...updates } : null,
        })),
    }),
    {
      name: "tiktrend-user",
      storage: createJSONStorage(() => localStorage),
      partialize: (state: UserState) => ({
        user: state.user,
        license: state.license,
        isAuthenticated: state.isAuthenticated,
        theme: state.theme,
      }),
    }
  )
);
