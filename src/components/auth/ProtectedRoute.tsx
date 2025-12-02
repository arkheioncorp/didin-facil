import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useUserStore } from "@/stores";
import { useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import type { AppSettings } from "@/types";

// Check if running in Tauri environment
const isTauri = (): boolean => {
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
};

// Check if running in development mode
const isDevelopment = (): boolean => {
  return import.meta.env.DEV || import.meta.env.MODE === 'development';
};

export const ProtectedRoute = () => {
  const isAuthenticated = useUserStore((state) => state.isAuthenticated);
  const hasHydrated = useUserStore((state) => state.hasHydrated);
  const setHasHydrated = useUserStore((state) => state.setHasHydrated);
  const location = useLocation();
  const [isReady, setIsReady] = useState(false);
  const [setupComplete, setSetupComplete] = useState<boolean | null>(null);

  // Check if setup is complete
  useEffect(() => {
    const checkSetup = async () => {
      // In non-Tauri environment (browser), skip setup check
      if (!isTauri()) {
        setSetupComplete(true);
        return;
      }
      
      try {
        const settings = await invoke<AppSettings>("get_settings");
        setSetupComplete(settings.setupComplete ?? false);
      } catch (error) {
        console.error("Failed to check setup status:", error);
        // If we can't read settings, assume setup is needed
        setSetupComplete(false);
      }
    };
    
    checkSetup();
  }, []);

  // Ensure hydration completes within a reasonable time
  useEffect(() => {
    if (hasHydrated && setupComplete !== null) {
      setIsReady(true);
    } else {
      // Fallback: if hydration takes too long, consider it complete
      const timeout = setTimeout(() => {
        // Force hydration if it hasn't completed
        if (!hasHydrated) {
          setHasHydrated(true);
        }
        setIsReady(true);
      }, 300); // Reduced timeout for faster loading
      return () => clearTimeout(timeout);
    }
  }, [hasHydrated, setupComplete, setHasHydrated]);

  if (!isReady) {
    return (
      <div
        className="flex min-h-screen items-center justify-center"
        data-testid="auth-loading"
      >
        <span className="sr-only">Carregando</span>
      </div>
    );
  }

  // Redirect to setup if not complete (and not already on setup page)
  if (setupComplete === false && location.pathname !== "/setup") {
    return <Navigate to="/setup" replace />;
  }

  // In development mode or trial mode, allow access without authentication
  // This enables testing and demo functionality
  if (isDevelopment() && !isAuthenticated) {
    // Allow access in dev mode without requiring login
    return <Outlet />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
};
