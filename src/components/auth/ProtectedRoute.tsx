import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useUserStore } from "@/stores";
import { useEffect, useState } from "react";
import { invoke } from "@tauri-apps/api/core";
import type { AppSettings } from "@/types";

export const ProtectedRoute = () => {
  const isAuthenticated = useUserStore((state) => state.isAuthenticated);
  const hasHydrated = useUserStore((state) => state.hasHydrated);
  const location = useLocation();
  const [isReady, setIsReady] = useState(false);
  const [setupComplete, setSetupComplete] = useState<boolean | null>(null);

  // Check if setup is complete
  useEffect(() => {
    const checkSetup = async () => {
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
        setIsReady(true);
      }, 500);
      return () => clearTimeout(timeout);
    }
  }, [hasHydrated, setupComplete]);

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

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
};
