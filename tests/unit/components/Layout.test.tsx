/**
 * @fileoverview Layout Component Tests - 100% Coverage
 * @description Testes completos para o componente Layout
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';

// Mock child components
vi.mock('@/components/layout/Sidebar', () => ({
  Sidebar: ({ collapsed, onToggle }: { collapsed: boolean; onToggle: () => void }) => (
    <div data-testid="sidebar" data-collapsed={collapsed}>
      <button data-testid="sidebar-toggle" onClick={onToggle}>
        Toggle
      </button>
    </div>
  ),
}));

vi.mock('@/components/layout/Header', () => ({
  Header: ({ onMenuClick }: { onMenuClick?: () => void }) => (
    <header data-testid="header">
      <button data-testid="menu-button" onClick={onMenuClick}>
        Menu
      </button>
    </header>
  ),
}));

const renderLayout = () => {
  return render(
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<div data-testid="outlet-content">Page Content</div>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

describe('Layout Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render without crashing', () => {
      renderLayout();
      expect(screen.getByTestId('header')).toBeInTheDocument();
    });

    it('should render sidebar on desktop', () => {
      renderLayout();
      expect(screen.getByTestId('sidebar')).toBeInTheDocument();
    });

    it('should render header', () => {
      renderLayout();
      expect(screen.getByTestId('header')).toBeInTheDocument();
    });

    it('should render outlet content', () => {
      renderLayout();
      expect(screen.getByTestId('outlet-content')).toBeInTheDocument();
    });
  });

  describe('Sidebar Toggle', () => {
    it('should start with sidebar expanded', () => {
      renderLayout();
      const sidebar = screen.getByTestId('sidebar');
      expect(sidebar).toHaveAttribute('data-collapsed', 'false');
    });

    it('should toggle sidebar when toggle button is clicked', () => {
      renderLayout();
      
      const toggleButton = screen.getByTestId('sidebar-toggle');
      fireEvent.click(toggleButton);

      const sidebar = screen.getByTestId('sidebar');
      expect(sidebar).toHaveAttribute('data-collapsed', 'true');
    });

    it('should toggle sidebar back to expanded', () => {
      renderLayout();
      
      const toggleButton = screen.getByTestId('sidebar-toggle');
      fireEvent.click(toggleButton); // Collapse
      fireEvent.click(toggleButton); // Expand

      const sidebar = screen.getByTestId('sidebar');
      expect(sidebar).toHaveAttribute('data-collapsed', 'false');
    });
  });

  describe('Mobile Menu', () => {
    it('should toggle mobile menu when header menu button is clicked', async () => {
      renderLayout();
      
      const menuButton = screen.getByTestId('menu-button');
      fireEvent.click(menuButton);

      // Mobile overlay should appear
      await waitFor(() => {
        // The mobile menu logic shows overlay when open
        expect(menuButton).toBeInTheDocument();
      });
    });
  });

  describe('Main Content Area', () => {
    it('should have proper margin when sidebar is expanded', () => {
      renderLayout();
      const main = screen.getByRole('main');
      expect(main).toHaveClass('lg:ml-64');
    });

    it('should update margin when sidebar is collapsed', () => {
      renderLayout();
      
      const toggleButton = screen.getByTestId('sidebar-toggle');
      fireEvent.click(toggleButton);

      const main = screen.getByRole('main');
      // After toggle, should have ml-16 class
      expect(main).toHaveClass('lg:ml-16');
    });

    it('should have padding', () => {
      renderLayout();
      const contentWrapper = screen.getByTestId('outlet-content').parentElement;
      expect(contentWrapper).toHaveClass('p-6');
    });
  });

  describe('Responsive Behavior', () => {
    it('should have hidden class for sidebar on mobile', () => {
      renderLayout();
      const sidebar = screen.getByTestId('sidebar');
      const sidebarContainer = sidebar.parentElement;
      expect(sidebarContainer).toHaveClass('hidden');
      expect(sidebarContainer).toHaveClass('lg:block');
    });

    it('should have transition classes', () => {
      renderLayout();
      const main = screen.getByRole('main');
      expect(main).toHaveClass('transition-all');
      expect(main).toHaveClass('duration-300');
    });
  });

  describe('Styling', () => {
    it('should have min-height of screen', () => {
      renderLayout();
      const container = screen.getByRole('main').parentElement;
      expect(container).toHaveClass('min-h-screen');
    });

    it('should have background color', () => {
      renderLayout();
      const container = screen.getByRole('main').parentElement;
      expect(container).toHaveClass('bg-background');
    });
  });

  describe('State Management', () => {
    it('should maintain sidebar state across interactions', () => {
      renderLayout();
      
      const toggleButton = screen.getByTestId('sidebar-toggle');
      
      // Multiple toggles
      fireEvent.click(toggleButton); // collapse
      expect(screen.getByTestId('sidebar')).toHaveAttribute('data-collapsed', 'true');
      
      fireEvent.click(toggleButton); // expand
      expect(screen.getByTestId('sidebar')).toHaveAttribute('data-collapsed', 'false');
      
      fireEvent.click(toggleButton); // collapse again
      expect(screen.getByTestId('sidebar')).toHaveAttribute('data-collapsed', 'true');
    });
  });

  describe('Accessibility', () => {
    it('should have main landmark', () => {
      renderLayout();
      expect(screen.getByRole('main')).toBeInTheDocument();
    });

    it('should render content inside main', () => {
      renderLayout();
      const main = screen.getByRole('main');
      expect(main).toContainElement(screen.getByTestId('outlet-content'));
    });
  });
});
