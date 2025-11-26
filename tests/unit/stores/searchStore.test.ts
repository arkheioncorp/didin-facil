/**
 * @fileoverview searchStore Unit Tests - 100% Coverage
 * @description Testes completos para o store de busca (searchStore)
 * 
 * Coverage Target: 100%
 * - All actions
 * - All state mutations
 * - Persistence
 * - Edge cases
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { act } from '@testing-library/react';

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
    get length() {
      return Object.keys(store).length;
    },
    key: vi.fn((index: number) => Object.keys(store)[index] || null),
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

// Import store after mocking localStorage
import { useSearchStore } from '@/stores/searchStore';

describe('SearchStore', () => {
  beforeEach(() => {
    localStorageMock.clear();
    vi.clearAllMocks();
    
    // Reset store to initial state
    const store = useSearchStore.getState();
    store.resetFilters();
    store.clearHistory();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Initial State', () => {
    it('should have default filters', () => {
      const state = useSearchStore.getState();
      
      expect(state.filters).toEqual({
        query: undefined,
        categories: [],
        priceMin: undefined,
        priceMax: undefined,
        salesMin: undefined,
        ratingMin: undefined,
        hasFreeShipping: undefined,
        isTrending: undefined,
        isOnSale: undefined,
        sortBy: 'trending',
        sortOrder: 'desc',
        page: 1,
        pageSize: 20,
      });
    });

    it('should have default config', () => {
      const state = useSearchStore.getState();
      
      expect(state.config).toEqual({
        maxResults: 50,
        includeImages: true,
        includeDescription: true,
        includeMetrics: true,
        autoSave: true,
        refreshInterval: 3600000,
      });
    });

    it('should have empty search history', () => {
      const state = useSearchStore.getState();
      expect(state.searchHistory).toEqual([]);
    });
  });

  describe('setFilters', () => {
    it('should update filters partially', () => {
      act(() => {
        useSearchStore.getState().setFilters({ query: 'test product' });
      });

      const state = useSearchStore.getState();
      expect(state.filters.query).toBe('test product');
      expect(state.filters.sortBy).toBe('trending'); // Other values unchanged
    });

    it('should update multiple filters at once', () => {
      act(() => {
        useSearchStore.getState().setFilters({
          query: 'test',
          priceMin: 10,
          priceMax: 100,
          categories: ['Electronics'],
        });
      });

      const state = useSearchStore.getState();
      expect(state.filters.query).toBe('test');
      expect(state.filters.priceMin).toBe(10);
      expect(state.filters.priceMax).toBe(100);
      expect(state.filters.categories).toEqual(['Electronics']);
    });

    it('should update boolean filters', () => {
      act(() => {
        useSearchStore.getState().setFilters({
          hasFreeShipping: true,
          isTrending: true,
          isOnSale: false,
        });
      });

      const state = useSearchStore.getState();
      expect(state.filters.hasFreeShipping).toBe(true);
      expect(state.filters.isTrending).toBe(true);
      expect(state.filters.isOnSale).toBe(false);
    });

    it('should update sort options', () => {
      act(() => {
        useSearchStore.getState().setFilters({
          sortBy: 'price_asc',
          sortOrder: 'asc',
        });
      });

      const state = useSearchStore.getState();
      expect(state.filters.sortBy).toBe('price_asc');
      expect(state.filters.sortOrder).toBe('asc');
    });

    it('should update pagination', () => {
      act(() => {
        useSearchStore.getState().setFilters({
          page: 3,
          pageSize: 50,
        });
      });

      const state = useSearchStore.getState();
      expect(state.filters.page).toBe(3);
      expect(state.filters.pageSize).toBe(50);
    });
  });

  describe('resetFilters', () => {
    it('should reset all filters to defaults', () => {
      // First set some filters
      act(() => {
        useSearchStore.getState().setFilters({
          query: 'test',
          priceMin: 50,
          categories: ['Fashion'],
          isTrending: true,
        });
      });

      // Then reset
      act(() => {
        useSearchStore.getState().resetFilters();
      });

      const state = useSearchStore.getState();
      expect(state.filters).toEqual({
        query: undefined,
        categories: [],
        priceMin: undefined,
        priceMax: undefined,
        salesMin: undefined,
        ratingMin: undefined,
        hasFreeShipping: undefined,
        isTrending: undefined,
        isOnSale: undefined,
        sortBy: 'trending',
        sortOrder: 'desc',
        page: 1,
        pageSize: 20,
      });
    });
  });

  describe('setConfig', () => {
    it('should update config partially', () => {
      act(() => {
        useSearchStore.getState().setConfig({ maxResults: 100 });
      });

      const state = useSearchStore.getState();
      expect(state.config.maxResults).toBe(100);
      expect(state.config.includeImages).toBe(true); // Unchanged
    });

    it('should update multiple config options', () => {
      act(() => {
        useSearchStore.getState().setConfig({
          maxResults: 200,
          includeImages: false,
          includeDescription: false,
          autoSave: false,
        });
      });

      const state = useSearchStore.getState();
      expect(state.config.maxResults).toBe(200);
      expect(state.config.includeImages).toBe(false);
      expect(state.config.includeDescription).toBe(false);
      expect(state.config.autoSave).toBe(false);
    });

    it('should update refresh interval', () => {
      act(() => {
        useSearchStore.getState().setConfig({
          refreshInterval: 7200000, // 2 hours
        });
      });

      const state = useSearchStore.getState();
      expect(state.config.refreshInterval).toBe(7200000);
    });
  });

  describe('Search History', () => {
    describe('addToHistory', () => {
      it('should add new query to history', () => {
        act(() => {
          useSearchStore.getState().addToHistory('test query');
        });

        const state = useSearchStore.getState();
        expect(state.searchHistory).toContain('test query');
        expect(state.searchHistory.length).toBe(1);
      });

      it('should add queries at the beginning', () => {
        act(() => {
          useSearchStore.getState().addToHistory('first');
          useSearchStore.getState().addToHistory('second');
        });

        const state = useSearchStore.getState();
        expect(state.searchHistory[0]).toBe('second');
        expect(state.searchHistory[1]).toBe('first');
      });

      it('should not duplicate queries', () => {
        act(() => {
          useSearchStore.getState().addToHistory('test');
          useSearchStore.getState().addToHistory('other');
          useSearchStore.getState().addToHistory('test'); // Duplicate
        });

        const state = useSearchStore.getState();
        expect(state.searchHistory.filter(q => q === 'test').length).toBe(1);
        expect(state.searchHistory[0]).toBe('test'); // Moved to front
      });

      it('should limit history to 20 items', () => {
        act(() => {
          for (let i = 0; i < 25; i++) {
            useSearchStore.getState().addToHistory(`query ${i}`);
          }
        });

        const state = useSearchStore.getState();
        expect(state.searchHistory.length).toBe(20);
        expect(state.searchHistory[0]).toBe('query 24'); // Most recent
      });

      it('should handle empty queries', () => {
        act(() => {
          useSearchStore.getState().addToHistory('');
        });

        const state = useSearchStore.getState();
        expect(state.searchHistory).toContain('');
      });

      it('should handle special characters', () => {
        act(() => {
          useSearchStore.getState().addToHistory('test @#$ special!');
        });

        const state = useSearchStore.getState();
        expect(state.searchHistory).toContain('test @#$ special!');
      });
    });

    describe('clearHistory', () => {
      it('should clear all search history', () => {
        // Add some history
        act(() => {
          useSearchStore.getState().addToHistory('query 1');
          useSearchStore.getState().addToHistory('query 2');
        });

        // Clear history
        act(() => {
          useSearchStore.getState().clearHistory();
        });

        const state = useSearchStore.getState();
        expect(state.searchHistory).toEqual([]);
      });

      it('should work when history is already empty', () => {
        act(() => {
          useSearchStore.getState().clearHistory();
        });

        const state = useSearchStore.getState();
        expect(state.searchHistory).toEqual([]);
      });
    });
  });

  describe('Persistence', () => {
    it('should persist filters to localStorage', async () => {
      act(() => {
        useSearchStore.getState().setFilters({ query: 'persistent query' });
      });

      // Check localStorage was called
      await new Promise(resolve => setTimeout(resolve, 0));
      expect(localStorageMock.setItem).toHaveBeenCalled();
    });

    it('should persist config to localStorage', async () => {
      act(() => {
        useSearchStore.getState().setConfig({ maxResults: 150 });
      });

      await new Promise(resolve => setTimeout(resolve, 0));
      expect(localStorageMock.setItem).toHaveBeenCalled();
    });

    it('should persist search history to localStorage', async () => {
      act(() => {
        useSearchStore.getState().addToHistory('persistent search');
      });

      await new Promise(resolve => setTimeout(resolve, 0));
      expect(localStorageMock.setItem).toHaveBeenCalled();
    });
  });

  describe('Edge Cases', () => {
    it('should handle undefined values in setFilters', () => {
      act(() => {
        useSearchStore.getState().setFilters({
          query: undefined,
          priceMin: undefined,
        });
      });

      const state = useSearchStore.getState();
      expect(state.filters.query).toBeUndefined();
      expect(state.filters.priceMin).toBeUndefined();
    });

    it('should handle null-like values', () => {
      act(() => {
        useSearchStore.getState().setFilters({
          salesMin: 0,
          ratingMin: 0,
        });
      });

      const state = useSearchStore.getState();
      expect(state.filters.salesMin).toBe(0);
      expect(state.filters.ratingMin).toBe(0);
    });

    it('should handle negative values', () => {
      act(() => {
        useSearchStore.getState().setFilters({
          priceMin: -10,
          page: -1,
        });
      });

      const state = useSearchStore.getState();
      expect(state.filters.priceMin).toBe(-10);
      expect(state.filters.page).toBe(-1);
    });

    it('should handle large numbers', () => {
      act(() => {
        useSearchStore.getState().setFilters({
          priceMax: 999999999,
          salesMin: Number.MAX_SAFE_INTEGER,
        });
      });

      const state = useSearchStore.getState();
      expect(state.filters.priceMax).toBe(999999999);
      expect(state.filters.salesMin).toBe(Number.MAX_SAFE_INTEGER);
    });

    it('should handle multiple categories', () => {
      act(() => {
        useSearchStore.getState().setFilters({
          categories: ['Electronics', 'Fashion', 'Home', 'Beauty'],
        });
      });

      const state = useSearchStore.getState();
      expect(state.filters.categories).toHaveLength(4);
      expect(state.filters.categories).toContain('Beauty');
    });
  });

  describe('Complex Scenarios', () => {
    it('should handle rapid state changes', () => {
      act(() => {
        for (let i = 0; i < 100; i++) {
          useSearchStore.getState().setFilters({ page: i });
        }
      });

      const state = useSearchStore.getState();
      expect(state.filters.page).toBe(99);
    });

    it('should maintain state consistency after multiple operations', () => {
      act(() => {
        useSearchStore.getState().setFilters({ query: 'test', priceMin: 10 });
        useSearchStore.getState().addToHistory('test');
        useSearchStore.getState().setConfig({ maxResults: 100 });
        useSearchStore.getState().setFilters({ priceMax: 50 });
      });

      const state = useSearchStore.getState();
      expect(state.filters.query).toBe('test');
      expect(state.filters.priceMin).toBe(10);
      expect(state.filters.priceMax).toBe(50);
      expect(state.config.maxResults).toBe(100);
      expect(state.searchHistory).toContain('test');
    });

    it('should handle interleaved operations', () => {
      act(() => {
        useSearchStore.getState().setFilters({ query: 'first' });
        useSearchStore.getState().addToHistory('first');
        useSearchStore.getState().resetFilters();
        useSearchStore.getState().addToHistory('second');
        useSearchStore.getState().setFilters({ query: 'third' });
      });

      const state = useSearchStore.getState();
      expect(state.filters.query).toBe('third');
      expect(state.searchHistory).toContain('first');
      expect(state.searchHistory).toContain('second');
    });
  });
});
