import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "@/components/layout";
import { SetupWizard, ProtectedRoute } from "@/components";
import {
  Dashboard,
  Search,
  Products,
  Coleta,
  Favorites,
  Copy,
  Settings,
  Profile,
  Login,
  Subscription,
  SellerBot,
  WhatsappPage,
  SocialDashboard,
  InstagramAutomation,
  TikTokAutomation,
  YouTubeAutomation,
  ChatbotBuilder,
  Scheduler,
  DLQPage,
  CRMDashboard,
  Pipeline,
  MetricsPage,
  AnalyticsDashboard,
  ContentTemplates,
  MultiAccountManager,
  APIDocumentation,
} from "@/pages";
import { ThemeProvider } from "@/components/providers";
import { Toaster } from "@/components/ui/toaster";
import ErrorBoundary from "@/components/ErrorBoundary";
import { NotificationsProvider } from "@/hooks/use-notifications";
import { analytics } from "@/lib/analytics";
import { useEffect } from "react";

function App() {
  useEffect(() => {
    analytics.init();
  }, []);

  return (
    <ThemeProvider defaultTheme="system">
      <NotificationsProvider>
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
                <Route path="coleta" element={<Coleta />} />
                <Route path="favorites" element={<Favorites />} />
                <Route path="copy" element={<Copy />} />
                <Route path="whatsapp" element={<WhatsappPage />} />
                <Route path="seller-bot" element={<SellerBot />} />

                {/* Social Suite Routes */}
                <Route path="social">
                  <Route index element={<SocialDashboard />} />
                  <Route path="instagram" element={<InstagramAutomation />} />
                  <Route path="tiktok" element={<TikTokAutomation />} />
                  <Route path="youtube" element={<YouTubeAutomation />} />
                </Route>

                {/* Automation Routes */}
                <Route path="automation">
                  <Route path="chatbot" element={<ChatbotBuilder />} />
                  <Route path="scheduler" element={<Scheduler />} />
                  <Route path="dlq" element={<DLQPage />} />
                </Route>

                {/* CRM Routes */}
                <Route path="crm">
                  <Route index element={<CRMDashboard />} />
                  <Route path="pipeline" element={<Pipeline />} />
                </Route>

                {/* Admin Routes */}
                <Route path="admin">
                  <Route path="metrics" element={<MetricsPage />} />
                  <Route path="analytics" element={<AnalyticsDashboard />} />
                  <Route path="templates" element={<ContentTemplates />} />
                  <Route path="accounts" element={<MultiAccountManager />} />
                  <Route path="docs" element={<APIDocumentation />} />
                </Route>

                <Route path="settings" element={<Settings />} />
                <Route path="profile" element={<Profile />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </ErrorBoundary>
      <Toaster />
    </NotificationsProvider>
  </ThemeProvider>
  );
} export default App;
