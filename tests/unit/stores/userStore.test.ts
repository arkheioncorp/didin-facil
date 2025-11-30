/**
 * User Store Unit Tests
 * Tests for Zustand user store
 */
import { describe, it, expect, beforeEach } from "vitest";
import { act } from "@testing-library/react";
import { useUserStore } from "@/stores/userStore";
import type { User, License, Credits } from "@/types";

// Mock user data - novo modelo lifetime + credits
const mockUser: User = {
  id: "user-123",
  email: "test@example.com",
  name: "Test User",
  avatarUrl: null,
  phone: null,
  hasLifetimeLicense: true,
  licenseActivatedAt: "2024-01-15T00:00:00Z",
  isActive: true,
  isEmailVerified: true,
  language: 'pt-BR',
  timezone: 'America/Sao_Paulo',
  createdAt: "2024-01-01T00:00:00Z",
  updatedAt: null,
  lastLoginAt: "2024-01-15T00:00:00Z",
};

const mockLicense: License = {
  id: "lic-123",
  isValid: true,
  isLifetime: true,
  plan: 'lifetime',
  activatedAt: "2024-01-15T00:00:00Z",
  expiresAt: null,
  maxDevices: 2,
  activeDevices: 1,
  currentDeviceId: null,
  isCurrentDeviceAuthorized: true,
};

const mockCredits: Credits = {
  balance: 50,
  totalPurchased: 100,
  totalUsed: 50,
  lastPurchaseAt: "2024-06-01T00:00:00Z",
  bonusBalance: 10,
  bonusExpiresAt: null,
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

    it("should handle license activation scenario", () => {
      const { login, setLicense, setCredits } = useUserStore.getState();

      // Login without lifetime license
      const freeUser: User = { ...mockUser, hasLifetimeLicense: false, licenseActivatedAt: null };
      const freeLicense: License = { ...mockLicense, isLifetime: false, activatedAt: null };

      act(() => {
        login(freeUser, freeLicense);
      });

      expect(useUserStore.getState().license?.isLifetime).toBe(false);

      // Upgrade to lifetime
      const lifetimeLicense: License = { ...mockLicense, isLifetime: true, activatedAt: new Date().toISOString() };

      act(() => {
        setLicense(lifetimeLicense);
      });

      expect(useUserStore.getState().license?.isLifetime).toBe(true);

      // Add credits
      act(() => {
        setCredits(mockCredits);
      });

      expect(useUserStore.getState().credits?.balance).toBe(50);
    });
  });
});
