import * as React from "react";
import { Outlet } from "react-router-dom";
import { cn } from "@/lib/utils";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { Footer } from "./Footer";
import { Tutorial } from "@/components/features/Tutorial";

interface LayoutProps {
  children?: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = () => {
  const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = React.useState(false);

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  // Close mobile menu on resize to desktop
  React.useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth >= 1024 && mobileMenuOpen) {
        setMobileMenuOpen(false);
      }
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [mobileMenuOpen]);

  return (
    <div className="min-h-screen bg-background flex flex-col lg:flex-row">
      <Tutorial />
      
      {/* Desktop Sidebar - Sticky Position */}
      {/* Using sticky ensures it takes up space in the flow (pushing content) while staying pinned */}
      <aside
        className={cn(
          "hidden lg:block sticky top-0 h-screen z-40 shrink-0 transition-all duration-300 ease-in-out",
          sidebarCollapsed ? "w-16" : "w-56"
        )}
      >
        <Sidebar collapsed={sidebarCollapsed} onToggle={toggleSidebar} />
      </aside>

      {/* Mobile Sidebar Overlay */}
      {mobileMenuOpen && (
        <>
          <div
            className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden"
            onClick={toggleMobileMenu}
            data-testid="mobile-overlay"
          />
          <aside 
            className="fixed left-0 top-0 z-50 h-screen w-56 lg:hidden"
            data-testid="mobile-sidebar-container"
          >
            <Sidebar collapsed={false} onToggle={toggleMobileMenu} />
          </aside>
        </>
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0 min-h-screen">
        <Header onMenuClick={toggleMobileMenu} />
        
        <main className="flex-1 p-4 md:p-5 lg:p-6">
          <Outlet />
        </main>

        <Footer className="mt-auto" />
      </div>
    </div>
  );
};
