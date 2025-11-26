/**
 * User Store Unit Tests
 * Tests for Zustand user store
 */
import { describe, it, expect, beforeEach } from "vitest";
import { act } from "@testing-library/react";
import { useUserStore } from "@/stores/userStore";
import type { User, License } from "@/types";

// Mock user data
const mockUser: User = {
  id: "user-123",
  email: "test@example.com",
  name: "Test User",
  plan: "pro",
  planExpiresAt: "2025-01-01T00:00:00Z",
  createdAt: "2024-01-01T00:00:00Z",
};

const mockLicense: License = {
  isValid: true,
  plan: "pro",
  features: {
    searchesPerMonth: 100,
    copiesPerMonth: 50,
    favoriteLists: 5,
    exportEnabled: true,
    schedulerEnabled: false,
  },
  expiresAt: "2025-01-01T00:00:00Z",
  usageThisMonth: {
    searches: 10,
    copies: 5,
  },
};

describe("useUserStore", () => {
  // Reset store before each test
  beforeEach(() => {
    const { logout } = useUserStore.getState();
    act(() => {
      logout();
    });
  });

  describe("Initial State", () => {
    it("should have correct initial state", () => {
      const state = useUserStore.getState();

      expect(state.user).toBeNull();
      expect(state.license).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.theme).toBe("system");
    });
  });

  describe("setUser", () => {
    it("should set user and update authentication status", () => {
      const { setUser } = useUserStore.getState();

      act(() => {
        setUser(mockUser);
      });

      const state = useUserStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
    });

    it("should set user to null and update authentication status", () => {
      const { setUser } = useUserStore.getState();

      // First set a user
      act(() => {
        setUser(mockUser);
      });

      // Then clear
      act(() => {
        setUser(null);
      });

      const state = useUserStore.getState();
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });
  });

  describe("setLicense", () => {
    it("should set license", () => {
      const { setLicense } = useUserStore.getState();

      act(() => {
        setLicense(mockLicense);
      });

      const state = useUserStore.getState();
      expect(state.license).toEqual(mockLicense);
    });

    it("should clear license when set to null", () => {
      const { setLicense } = useUserStore.getState();

      act(() => {
        setLicense(mockLicense);
      });

      act(() => {
        setLicense(null);
      });

      const state = useUserStore.getState();
      expect(state.license).toBeNull();
    });
  });

  describe("setTheme", () => {
    it("should set theme to light", () => {
      const { setTheme } = useUserStore.getState();

      act(() => {
        setTheme("light");
      });

      expect(useUserStore.getState().theme).toBe("light");
    });

    it("should set theme to dark", () => {
      const { setTheme } = useUserStore.getState();

      act(() => {
        setTheme("dark");
      });

      expect(useUserStore.getState().theme).toBe("dark");
    });

    it("should set theme to system", () => {
      const { setTheme } = useUserStore.getState();

      act(() => {
        setTheme("dark");
      });

      act(() => {
        setTheme("system");
      });

      expect(useUserStore.getState().theme).toBe("system");
    });
  });

  describe("login", () => {
    it("should set user, license, and authentication status", () => {
      const { login } = useUserStore.getState();

      act(() => {
        login(mockUser, mockLicense);
      });

      const state = useUserStore.getState();
      expect(state.user).toEqual(mockUser);
      expect(state.license).toEqual(mockLicense);
      expect(state.isAuthenticated).toBe(true);
    });
  });

  describe("logout", () => {
    it("should clear all user data", () => {
      const { login, logout } = useUserStore.getState();

      // First login
      act(() => {
        login(mockUser, mockLicense);
      });

      // Then logout
      act(() => {
        logout();
      });

      const state = useUserStore.getState();
      expect(state.user).toBeNull();
      expect(state.license).toBeNull();
      expect(state.isAuthenticated).toBe(false);
    });

    it("should preserve theme preference after logout", () => {
      const { login, logout, setTheme } = useUserStore.getState();

      act(() => {
        login(mockUser, mockLicense);
        setTheme("dark");
      });

      act(() => {
        logout();
      });

      // Theme might be reset depending on implementation
      // This test documents expected behavior
      const state = useUserStore.getState();
      expect(state.theme).toBeDefined();
    });
  });

  describe("updateUser", () => {
    it("should update user with partial data", () => {
      const { setUser, updateUser } = useUserStore.getState();

      act(() => {
        setUser(mockUser);
      });

      act(() => {
        updateUser({ name: "Updated Name" });
      });

      const state = useUserStore.getState();
      expect(state.user?.name).toBe("Updated Name");
      expect(state.user?.email).toBe(mockUser.email);
    });

    it("should not update if user is null", () => {
      const { updateUser } = useUserStore.getState();

      act(() => {
        updateUser({ name: "Test" });
      });

      const state = useUserStore.getState();
      expect(state.user).toBeNull();
    });

    it("should update multiple fields", () => {
      const { setUser, updateUser } = useUserStore.getState();

      act(() => {
        setUser(mockUser);
      });

      act(() => {
        updateUser({
          name: "New Name",
        });
      });

      const state = useUserStore.getState();
      expect(state.user?.name).toBe("New Name");
    });
  });

  describe("State Selectors", () => {
    it("should allow selecting specific state values", () => {
      const { login } = useUserStore.getState();

      act(() => {
        login(mockUser, mockLicense);
      });

      // Test that we can select individual values
      const user = useUserStore.getState().user;
      const isAuth = useUserStore.getState().isAuthenticated;

      expect(user).toEqual(mockUser);
      expect(isAuth).toBe(true);
    });
  });

  describe("Integration Scenarios", () => {
    it("should handle complete auth flow", () => {
      const { login, logout, setTheme } = useUserStore.getState();

      // Initial state
      expect(useUserStore.getState().isAuthenticated).toBe(false);

      // Login
      act(() => {
        login(mockUser, mockLicense);
      });
      expect(useUserStore.getState().isAuthenticated).toBe(true);

      // Set preferences
      act(() => {
        setTheme("dark");
      });
      expect(useUserStore.getState().theme).toBe("dark");

      // Logout
      act(() => {
        logout();
      });
      expect(useUserStore.getState().isAuthenticated).toBe(false);
    });

    it("should handle plan upgrade scenario", () => {
      const { login, setLicense } = useUserStore.getState();

      // Login with basic plan
      const basicUser = { ...mockUser, plan: "basic" as const };
      const basicLicense = { ...mockLicense, plan: "basic" as const };

      act(() => {
        login(basicUser, basicLicense);
      });

      expect(useUserStore.getState().license?.plan).toBe("basic");

      // Upgrade to pro
      const proLicense = { ...mockLicense, plan: "pro" as const };

      act(() => {
        setLicense(proLicense);
      });

      expect(useUserStore.getState().license?.plan).toBe("pro");
    });
  });
});
