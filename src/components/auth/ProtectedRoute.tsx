import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useUserStore } from "@/stores";
import { useEffect, useState } from "react";

export const ProtectedRoute = () => {
  const isAuthenticated = useUserStore((state) => state.isAuthenticated);
  const hasHydrated = useUserStore((state) => state.hasHydrated);
  const location = useLocation();
  const [isReady, setIsReady] = useState(false);

  // Ensure hydration completes within a reasonable time
  useEffect(() => {
    if (hasHydrated) {
      setIsReady(true);
    } else {
      // Fallback: if hydration takes too long, consider it complete
      const timeout = setTimeout(() => {
        setIsReady(true);
      }, 500);
      return () => clearTimeout(timeout);
    }
  }, [hasHydrated]);

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

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
};
