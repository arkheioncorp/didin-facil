/**
 * @fileoverview Header Component Tests - 100% Coverage
 * @description Testes completos para o componente Header
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { Header } from '@/components/layout/Header';
import { NotificationsProvider } from '@/hooks/use-notifications';

// Mock TutorialProvider
vi.mock('@/components/tutorial', () => ({
  TutorialHelpButton: () => <button data-testid="tutorial-help">Help</button>,
  TutorialProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useTutorial: () => ({
    isActive: false,
    startTutorial: vi.fn(),
    endTutorial: vi.fn(),
  }),
}));

// Mock icons
vi.mock('@/components/icons', () => ({
  SearchIcon: ({ size: _size }: { size: number }) => <span data-testid="search-icon">SearchIcon</span>,
  MenuIcon: ({ size: _size }: { size: number }) => <span data-testid="menu-icon">MenuIcon</span>,
}));

// Mock UI components
vi.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, className, ...props }: any) => (
    <button onClick={onClick} className={className} {...props}>
      {children}
    </button>
  ),
}));

vi.mock('@/components/ui/input', () => ({
  Input: ({ placeholder, className, icon }: any) => (
    <div className={className}>
      {icon}
      <input placeholder={placeholder} data-testid="search-input" />
    </div>
  ),
}));

// Mock NotificationBell to avoid complex dependencies
vi.mock('@/components/NotificationBell', () => ({
  NotificationBell: () => <button data-testid="notification-bell">Notifications</button>,
}));

const renderHeader = (props = {}) => {
  return render(
    <BrowserRouter>
      <NotificationsProvider>
        <Header {...props} />
      </NotificationsProvider>
    </BrowserRouter>
  );
};

describe('Header Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Rendering', () => {
    it('should render without crashing', () => {
      renderHeader();
      expect(screen.getByRole('banner')).toBeInTheDocument();
    });

    it('should render with default props', () => {
      renderHeader();
      expect(screen.getByTestId('menu-icon')).toBeInTheDocument();
    });

    it('should render title when provided', () => {
      renderHeader({ title: 'Test Title' });
      expect(screen.getByText('Test Title')).toBeInTheDocument();
    });

    it('should not render title when not provided', () => {
      renderHeader();
      expect(screen.queryByRole('heading')).not.toBeInTheDocument();
    });

    it('should render search input by default', () => {
      renderHeader();
      expect(screen.getByTestId('search-input')).toBeInTheDocument();
    });

    it('should not render search when showSearch is false', () => {
      renderHeader({ showSearch: false });
      expect(screen.queryByTestId('search-input')).not.toBeInTheDocument();
    });

    it('should render menu button', () => {
      renderHeader();
      expect(screen.getByTestId('menu-icon')).toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
    it('should call onMenuClick when menu button is clicked', () => {
      const onMenuClick = vi.fn();
      renderHeader({ onMenuClick });

      const menuButton = screen.getByTestId('menu-icon').parentElement;
      fireEvent.click(menuButton!);

      expect(onMenuClick).toHaveBeenCalledTimes(1);
    });

    it('should not throw when menu button clicked without handler', () => {
      renderHeader();
      const menuButton = screen.getByTestId('menu-icon').parentElement;
      expect(() => fireEvent.click(menuButton!)).not.toThrow();
    });
  });

  describe('Styling', () => {
    it('should have sticky positioning', () => {
      renderHeader();
      const header = screen.getByRole('banner');
      expect(header).toHaveClass('sticky');
    });

    it('should have proper z-index', () => {
      renderHeader();
      const header = screen.getByRole('banner');
      expect(header).toHaveClass('z-30');
    });

    it('should have border bottom', () => {
      renderHeader();
      const header = screen.getByRole('banner');
      expect(header).toHaveClass('border-b');
    });
  });

  describe('Accessibility', () => {
    it('should have banner role', () => {
      renderHeader();
      expect(screen.getByRole('banner')).toBeInTheDocument();
    });

    it('should have accessible title when provided', () => {
      renderHeader({ title: 'Dashboard' });
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });
  });

  describe('Edge Cases', () => {
    it('should handle empty string title', () => {
      renderHeader({ title: '' });
      // Empty string is falsy, so no heading should render
      expect(screen.queryByRole('heading')).not.toBeInTheDocument();
    });

    it('should handle very long title', () => {
      const longTitle = 'A'.repeat(200);
      renderHeader({ title: longTitle });
      expect(screen.getByText(longTitle)).toBeInTheDocument();
    });

    it('should handle special characters in title', () => {
      renderHeader({ title: 'Test <>&"\'`' });
      expect(screen.getByText("Test <>&\"'`")).toBeInTheDocument();
    });
  });
});
