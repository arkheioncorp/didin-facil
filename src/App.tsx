import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Suspense, lazy, useEffect } from "react";
import { Layout } from "@/components/layout";
import { SetupWizard, ProtectedRoute } from "@/components";
import { ThemeProvider } from "@/components/providers";
import { Toaster } from "@/components/ui/toaster";
import ErrorBoundary from "@/components/ErrorBoundary";
import { NotificationsProvider } from "@/hooks/use-notifications";
import { analytics } from "@/lib/analytics";

// Lazy load pages for code-splitting
const Dashboard = lazy(() => import("@/pages/Dashboard"));
const Search = lazy(() => import("@/pages/Search"));
const Products = lazy(() => import("@/pages/Products"));
const Coleta = lazy(() => import("@/pages/Coleta"));
const Favorites = lazy(() => import("@/pages/Favorites"));
const Copy = lazy(() => import("@/pages/Copy"));
const Settings = lazy(() => import("@/pages/Settings"));
const Profile = lazy(() => import("@/pages/Profile"));
const Login = lazy(() => import("@/pages/Login"));
const Subscription = lazy(() => import("@/pages/Subscription"));
const SellerBot = lazy(() => import("@/pages/SellerBot"));
const WhatsappPage = lazy(() => import("@/pages/Whatsapp"));
const SocialDashboard = lazy(() => import("@/pages/social/SocialDashboard"));
const InstagramAutomation = lazy(() => import("@/pages/social/InstagramAutomation"));
const TikTokAutomation = lazy(() => import("@/pages/social/TikTokAutomation"));
const YouTubeAutomation = lazy(() => import("@/pages/social/YouTubeAutomation"));
const ChatbotBuilder = lazy(() => import("@/pages/automation/ChatbotBuilder"));
const Scheduler = lazy(() => import("@/pages/automation/Scheduler"));
const DLQPage = lazy(() => import("@/pages/automation/DLQ"));
const CRMDashboard = lazy(() => import("@/pages/crm/CRMDashboard"));
const Pipeline = lazy(() => import("@/pages/crm/Pipeline"));
const MetricsPage = lazy(() => import("@/pages/admin/Metrics"));
// Note: These pages don't exist yet - commenting out for now
// const AnalyticsDashboard = lazy(() => import("@/pages/admin/AnalyticsDashboard"));
// const ContentTemplates = lazy(() => import("@/pages/admin/ContentTemplates"));
// const MultiAccountManager = lazy(() => import("@/pages/admin/MultiAccountManager"));
// const APIDocumentation = lazy(() => import("@/pages/admin/APIDocumentation"));

// Loading fallback component
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-[400px]">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
  </div>
);

function App() {
  useEffect(() => {
    analytics.init();
  }, []);

  return (
    <ThemeProvider defaultTheme="system">
      <NotificationsProvider>
        <ErrorBoundary>
          <BrowserRouter>
            <Suspense fallback={<PageLoader />}>
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
                      {/* TODO: Create these pages 
                      <Route path="analytics" element={<AnalyticsDashboard />} />
                      <Route path="templates" element={<ContentTemplates />} />
                      <Route path="accounts" element={<MultiAccountManager />} />
                      <Route path="docs" element={<APIDocumentation />} />
                      */}
                    </Route>

                    <Route path="settings" element={<Settings />} />
                    <Route path="profile" element={<Profile />} />
                  </Route>
                </Route>
              </Routes>
            </Suspense>
          </BrowserRouter>
        </ErrorBoundary>
        <Toaster />
      </NotificationsProvider>
    </ThemeProvider>
  );
}

export default App;
