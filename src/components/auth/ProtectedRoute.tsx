import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useUserStore } from "@/stores";

export const ProtectedRoute = () => {
  const isAuthenticated = useUserStore((state) => state.isAuthenticated);
  const hasHydrated = useUserStore((state) => state.hasHydrated);
  const location = useLocation();

  if (!hasHydrated) {
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
