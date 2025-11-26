import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useUserStore } from "@/stores";

export const ProtectedRoute = () => {
  const { isAuthenticated } = useUserStore();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <Outlet />;
};
