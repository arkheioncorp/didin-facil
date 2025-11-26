import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "@/components/layout";
import { SetupWizard, ProtectedRoute } from "@/components";
import {
  Dashboard,
  Search,
  Products,
  Favorites,
  Copy,
  Settings,
  Profile,
  Login,
  Subscription,
} from "@/pages";
import { ToastProvider, ToastViewport } from "@/components/ui";
import { ThemeProvider } from "@/components/providers";
import ErrorBoundary from "@/components/ErrorBoundary";
import { analytics } from "@/lib/analytics";
import { useEffect } from "react";

function App() {
  useEffect(() => {
    analytics.init();
  }, []);

  return (
    <ThemeProvider defaultTheme="system">
      <ToastProvider>
        <ErrorBoundary>
          <BrowserRouter>
            <Routes>
              {/* Auth routes (no layout) */}
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Login />} />
              <Route path="/subscription" element={<Subscription />} />
              <Route path="/setup" element={<SetupWizard />} />

              {/* App routes (with layout) */}
              <Route element={<ProtectedRoute />}>
                <Route path="/" element={<Layout />}>
                  <Route index element={<Dashboard />} />
                  <Route path="search" element={<Search />} />
                  <Route path="products" element={<Products />} />
                  <Route path="favorites" element={<Favorites />} />
                  <Route path="copy" element={<Copy />} />
                  <Route path="settings" element={<Settings />} />
                  <Route path="profile" element={<Profile />} />
                </Route>
              </Route>
            </Routes>
          </BrowserRouter>
        </ErrorBoundary>
        <ToastViewport />
      </ToastProvider>
    </ThemeProvider>
  );
} export default App;
