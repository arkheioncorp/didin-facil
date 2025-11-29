/**
 * @fileoverview favoritesStore Unit Tests - 100% Coverage
 * @description Testes completos para o store de favoritos (favoritesStore)
 *
 * Coverage Target: 100%
 * - All actions (add, remove, toggle, clear)
 * - Collections management
 * - Persistence
 * - Edge cases
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { act } from '@testing-library/react';
import type { Product } from '@/types';

// Import store
import { useFavoritesStore } from '@/stores/favoritesStore';

// Test helper: create mock product
const createMockProduct = (overrides: Partial<Product> = {}): Product => ({
  id: `product-${Math.random().toString(36).substring(7)}`,
  tiktokId: 'tiktok-123',
  title: 'Test Product',
  description: 'A test product description',
  price: 99.99,
  originalPrice: 129.99,
  currency: 'BRL',
  category: 'Electronics',
  subcategory: null,
  imageUrl: 'https://example.com/image.jpg',
  images: ['https://example.com/image.jpg'],
  videoUrl: 'https://example.com/video.mp4',
  productUrl: 'https://example.com/product',
  affiliateUrl: 'https://example.com/affiliate',
  sellerName: 'Test Seller',
  sellerRating: 4.5,
  productRating: 4.8,
  reviewsCount: 100,
  salesCount: 500,
  sales7d: 50,
  sales30d: 200,
  commissionRate: 10,
  hasFreeShipping: true,
  isTrending: true,
  isOnSale: true,
  inStock: true,
  collectedAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  ...overrides,
});

describe('FavoritesStore', () => {
  beforeEach(() => {
    window.localStorage.clear();
    vi.clearAllMocks();
    
    // Reset store to initial state
    const store = useFavoritesStore.getState();
    store.clearFavorites();
    // Clear all collections
    store.collections.forEach(c => store.deleteCollection(c.id));
  });

  afterEach(() => {
    // vi.restoreAllMocks(); // Removed to prevent clearing localStorage mock implementation
  });

  describe('Initial State', () => {
    it('should start with empty favorites', () => {
      const state = useFavoritesStore.getState();
      expect(state.favorites).toEqual([]);
    });

    it('should start with empty collections', () => {
      const state = useFavoritesStore.getState();
      expect(state.collections).toEqual([]);
    });
  });

  describe('addFavorite', () => {
    it('should add a product to favorites', () => {
      const product = createMockProduct({ id: 'product-1' });

      act(() => {
        useFavoritesStore.getState().addFavorite(product);
      });

      const state = useFavoritesStore.getState();
      expect(state.favorites).toHaveLength(1);
      expect(state.favorites[0].id).toBe('product-1');
    });

    it('should not add duplicate products', () => {
      const product = createMockProduct({ id: 'product-1' });

      act(() => {
        useFavoritesStore.getState().addFavorite(product);
        useFavoritesStore.getState().addFavorite(product);
      });

      const state = useFavoritesStore.getState();
      expect(state.favorites).toHaveLength(1);
    });

    it('should add multiple different products', () => {
      const product1 = createMockProduct({ id: 'product-1' });
      const product2 = createMockProduct({ id: 'product-2' });
      const product3 = createMockProduct({ id: 'product-3' });

      act(() => {
        useFavoritesStore.getState().addFavorite(product1);
        useFavoritesStore.getState().addFavorite(product2);
        useFavoritesStore.getState().addFavorite(product3);
      });

      const state = useFavoritesStore.getState();
      expect(state.favorites).toHaveLength(3);
    });

    it('should preserve product data completely', () => {
      const product = createMockProduct({
        id: 'product-special',
        title: 'Special Product',
        price: 199.99,
        category: 'Fashion',
      });

      act(() => {
        useFavoritesStore.getState().addFavorite(product);
      });

      const state = useFavoritesStore.getState();
      const savedProduct = state.favorites.find(p => p.id === 'product-special');
      expect(savedProduct?.title).toBe('Special Product');
      expect(savedProduct?.price).toBe(199.99);
      expect(savedProduct?.category).toBe('Fashion');
    });
  });

  describe('removeFavorite', () => {
    it('should remove a product from favorites', () => {
      const product = createMockProduct({ id: 'product-1' });

      act(() => {
        useFavoritesStore.getState().addFavorite(product);
        useFavoritesStore.getState().removeFavorite('product-1');
      });

      const state = useFavoritesStore.getState();
      expect(state.favorites).toHaveLength(0);
    });

    it('should only remove the specified product', () => {
      const product1 = createMockProduct({ id: 'product-1' });
      const product2 = createMockProduct({ id: 'product-2' });

      act(() => {
        useFavoritesStore.getState().addFavorite(product1);
        useFavoritesStore.getState().addFavorite(product2);
        useFavoritesStore.getState().removeFavorite('product-1');
      });

      const state = useFavoritesStore.getState();
      expect(state.favorites).toHaveLength(1);
      expect(state.favorites[0].id).toBe('product-2');
    });

    it('should handle removing non-existent product gracefully', () => {
      act(() => {
        useFavoritesStore.getState().removeFavorite('non-existent');
      });

      const state = useFavoritesStore.getState();
      expect(state.favorites).toHaveLength(0);
    });
  });

  describe('toggleFavorite', () => {
    it('should add product when not in favorites', () => {
      const product = createMockProduct({ id: 'product-1' });

      act(() => {
        useFavoritesStore.getState().toggleFavorite(product);
      });

      const state = useFavoritesStore.getState();
      expect(state.favorites).toHaveLength(1);
    });

    it('should remove product when already in favorites', () => {
      const product = createMockProduct({ id: 'product-1' });

      act(() => {
        useFavoritesStore.getState().addFavorite(product);
        useFavoritesStore.getState().toggleFavorite(product);
      });

      const state = useFavoritesStore.getState();
      expect(state.favorites).toHaveLength(0);
    });

    it('should toggle correctly multiple times', () => {
      const product = createMockProduct({ id: 'product-1' });

      act(() => {
        useFavoritesStore.getState().toggleFavorite(product);
      });
      expect(useFavoritesStore.getState().favorites).toHaveLength(1);

      act(() => {
        useFavoritesStore.getState().toggleFavorite(product);
      });
      expect(useFavoritesStore.getState().favorites).toHaveLength(0);

      act(() => {
        useFavoritesStore.getState().toggleFavorite(product);
      });
      expect(useFavoritesStore.getState().favorites).toHaveLength(1);
    });
  });

  describe('isFavorite', () => {
    it('should return true for favorited products', () => {
      const product = createMockProduct({ id: 'product-1' });

      act(() => {
        useFavoritesStore.getState().addFavorite(product);
      });

      expect(useFavoritesStore.getState().isFavorite('product-1')).toBe(true);
    });

    it('should return false for non-favorited products', () => {
      expect(useFavoritesStore.getState().isFavorite('non-existent')).toBe(false);
    });

    it('should return false after removing product', () => {
      const product = createMockProduct({ id: 'product-1' });

      act(() => {
        useFavoritesStore.getState().addFavorite(product);
        useFavoritesStore.getState().removeFavorite('product-1');
      });

      expect(useFavoritesStore.getState().isFavorite('product-1')).toBe(false);
    });
  });

  describe('clearFavorites', () => {
    it('should remove all favorites', () => {
      const product1 = createMockProduct({ id: 'product-1' });
      const product2 = createMockProduct({ id: 'product-2' });

      act(() => {
        useFavoritesStore.getState().addFavorite(product1);
        useFavoritesStore.getState().addFavorite(product2);
        useFavoritesStore.getState().clearFavorites();
      });

      const state = useFavoritesStore.getState();
      expect(state.favorites).toHaveLength(0);
    });

    it('should work when favorites are already empty', () => {
      act(() => {
        useFavoritesStore.getState().clearFavorites();
      });

      const state = useFavoritesStore.getState();
      expect(state.favorites).toHaveLength(0);
    });
  });

  describe('Collections', () => {
    describe('createCollection', () => {
      it('should create a new collection', () => {
        act(() => {
          useFavoritesStore.getState().createCollection('My Collection');
        });

        const state = useFavoritesStore.getState();
        expect(state.collections).toHaveLength(1);
        expect(state.collections[0].name).toBe('My Collection');
        expect(state.collections[0].productIds).toEqual([]);
      });

      it('should generate unique IDs for collections', () => {
        act(() => {
          useFavoritesStore.getState().createCollection('Collection 1');
          useFavoritesStore.getState().createCollection('Collection 2');
        });

        const state = useFavoritesStore.getState();
        expect(state.collections[0].id).not.toBe(state.collections[1].id);
      });

      it('should allow collections with same name', () => {
        act(() => {
          useFavoritesStore.getState().createCollection('Same Name');
          useFavoritesStore.getState().createCollection('Same Name');
        });

        const state = useFavoritesStore.getState();
        expect(state.collections).toHaveLength(2);
      });
    });

    describe('deleteCollection', () => {
      it('should delete a collection', () => {
        let collectionId: string;

        act(() => {
          useFavoritesStore.getState().createCollection('To Delete');
          collectionId = useFavoritesStore.getState().collections[0].id;
        });

        act(() => {
          useFavoritesStore.getState().deleteCollection(collectionId!);
        });

        const state = useFavoritesStore.getState();
        expect(state.collections).toHaveLength(0);
      });

      it('should only delete the specified collection', () => {
        act(() => {
          useFavoritesStore.getState().createCollection('Keep');
          useFavoritesStore.getState().createCollection('Delete');
        });

        const toDelete = useFavoritesStore.getState().collections.find(c => c.name === 'Delete');

        act(() => {
          useFavoritesStore.getState().deleteCollection(toDelete!.id);
        });

        const state = useFavoritesStore.getState();
        expect(state.collections).toHaveLength(1);
        expect(state.collections[0].name).toBe('Keep');
      });

      it('should handle deleting non-existent collection gracefully', () => {
        act(() => {
          useFavoritesStore.getState().deleteCollection('non-existent');
        });

        const state = useFavoritesStore.getState();
        expect(state.collections).toHaveLength(0);
      });
    });

    describe('addToCollection', () => {
      it('should add product to collection', () => {
        let collectionId: string;

        act(() => {
          useFavoritesStore.getState().createCollection('My Collection');
          collectionId = useFavoritesStore.getState().collections[0].id;
          useFavoritesStore.getState().addToCollection(collectionId, 'product-1');
        });

        const state = useFavoritesStore.getState();
        expect(state.collections[0].productIds).toContain('product-1');
      });

      it('should not add duplicate products to collection', () => {
        let collectionId: string;

        act(() => {
          useFavoritesStore.getState().createCollection('My Collection');
          collectionId = useFavoritesStore.getState().collections[0].id;
          useFavoritesStore.getState().addToCollection(collectionId, 'product-1');
          useFavoritesStore.getState().addToCollection(collectionId, 'product-1');
        });

        const state = useFavoritesStore.getState();
        expect(state.collections[0].productIds.filter(id => id === 'product-1')).toHaveLength(1);
      });

      it('should add multiple products to same collection', () => {
        let collectionId: string;

        act(() => {
          useFavoritesStore.getState().createCollection('My Collection');
          collectionId = useFavoritesStore.getState().collections[0].id;
          useFavoritesStore.getState().addToCollection(collectionId, 'product-1');
          useFavoritesStore.getState().addToCollection(collectionId, 'product-2');
          useFavoritesStore.getState().addToCollection(collectionId, 'product-3');
        });

        const state = useFavoritesStore.getState();
        expect(state.collections[0].productIds).toHaveLength(3);
      });

      it('should add same product to different collections', () => {
        act(() => {
          useFavoritesStore.getState().createCollection('Collection 1');
          useFavoritesStore.getState().createCollection('Collection 2');
        });

        const state = useFavoritesStore.getState();
        const col1Id = state.collections[0].id;
        const col2Id = state.collections[1].id;

        act(() => {
          useFavoritesStore.getState().addToCollection(col1Id, 'product-1');
          useFavoritesStore.getState().addToCollection(col2Id, 'product-1');
        });

        const updatedState = useFavoritesStore.getState();
        expect(updatedState.collections[0].productIds).toContain('product-1');
        expect(updatedState.collections[1].productIds).toContain('product-1');
      });
    });

    describe('removeFromCollection', () => {
      it('should remove product from collection', () => {
        let collectionId: string;

        act(() => {
          useFavoritesStore.getState().createCollection('My Collection');
          collectionId = useFavoritesStore.getState().collections[0].id;
          useFavoritesStore.getState().addToCollection(collectionId, 'product-1');
          useFavoritesStore.getState().addToCollection(collectionId, 'product-2');
          useFavoritesStore.getState().removeFromCollection(collectionId, 'product-1');
        });

        const state = useFavoritesStore.getState();
        expect(state.collections[0].productIds).not.toContain('product-1');
        expect(state.collections[0].productIds).toContain('product-2');
      });

      it('should handle removing non-existent product gracefully', () => {
        let collectionId: string;

        act(() => {
          useFavoritesStore.getState().createCollection('My Collection');
          collectionId = useFavoritesStore.getState().collections[0].id;
          useFavoritesStore.getState().removeFromCollection(collectionId, 'non-existent');
        });

        const state = useFavoritesStore.getState();
        expect(state.collections[0].productIds).toHaveLength(0);
      });
    });
  });

  describe('Persistence', () => {
    beforeEach(() => {
      vi.clearAllMocks();
    });

    it('should persist favorites to localStorage', async () => {
      const setItemSpy = vi.spyOn(window.localStorage, 'setItem');
      const product = createMockProduct({ id: 'product-1' });

      act(() => {
        useFavoritesStore.getState().addFavorite(product);
      });
      
      await new Promise(resolve => setTimeout(resolve, 10));
      expect(setItemSpy).toHaveBeenCalled();
    });

    it('should persist collections to localStorage', async () => {
      const setItemSpy = vi.spyOn(window.localStorage, 'setItem');
      act(() => {
        useFavoritesStore.getState().createCollection('Test Collection');
      });

      await new Promise(resolve => setTimeout(resolve, 10));
      expect(setItemSpy).toHaveBeenCalled();
    });
  });

  describe('Edge Cases', () => {
    it('should handle products with special characters in ID', () => {
      const product = createMockProduct({ id: 'product-!@#$%^&*()' });

      act(() => {
        useFavoritesStore.getState().addFavorite(product);
      });

      expect(useFavoritesStore.getState().isFavorite('product-!@#$%^&*()')).toBe(true);
    });

    it('should handle very long collection names', () => {
      const longName = 'A'.repeat(1000);

      act(() => {
        useFavoritesStore.getState().createCollection(longName);
      });

      const state = useFavoritesStore.getState();
      expect(state.collections[0].name).toBe(longName);
    });

    it('should handle empty collection name', () => {
      act(() => {
        useFavoritesStore.getState().createCollection('');
      });

      const state = useFavoritesStore.getState();
      expect(state.collections[0].name).toBe('');
    });

    it('should handle large number of favorites', () => {
      act(() => {
        for (let i = 0; i < 1000; i++) {
          const product = createMockProduct({ id: `product-${i}` });
          useFavoritesStore.getState().addFavorite(product);
        }
      });

      const state = useFavoritesStore.getState();
      expect(state.favorites).toHaveLength(1000);
    });

    it('should handle large number of collections', () => {
      act(() => {
        for (let i = 0; i < 100; i++) {
          useFavoritesStore.getState().createCollection(`Collection ${i}`);
        }
      });

      const state = useFavoritesStore.getState();
      expect(state.collections).toHaveLength(100);
    });
  });

  describe('Complex Scenarios', () => {
    it('should handle rapid add/remove operations', () => {
      const product = createMockProduct({ id: 'product-1' });

      act(() => {
        for (let i = 0; i < 50; i++) {
          useFavoritesStore.getState().addFavorite(product);
          useFavoritesStore.getState().removeFavorite(product.id);
        }
        useFavoritesStore.getState().addFavorite(product);
      });

      const state = useFavoritesStore.getState();
      expect(state.favorites).toHaveLength(1);
    });

    it('should maintain data integrity with mixed operations', () => {
      const product1 = createMockProduct({ id: 'product-1' });
      const product2 = createMockProduct({ id: 'product-2' });

      act(() => {
        // Add favorites
        useFavoritesStore.getState().addFavorite(product1);
        useFavoritesStore.getState().addFavorite(product2);
        
        // Create collections
        useFavoritesStore.getState().createCollection('Collection A');
        useFavoritesStore.getState().createCollection('Collection B');
      });

      const state = useFavoritesStore.getState();
      const colAId = state.collections.find(c => c.name === 'Collection A')!.id;
      const colBId = state.collections.find(c => c.name === 'Collection B')!.id;

      act(() => {
        // Add to collections
        useFavoritesStore.getState().addToCollection(colAId, 'product-1');
        useFavoritesStore.getState().addToCollection(colBId, 'product-1');
        useFavoritesStore.getState().addToCollection(colBId, 'product-2');
        
        // Toggle favorite
        useFavoritesStore.getState().toggleFavorite(product1);
        
        // Remove from one collection
        useFavoritesStore.getState().removeFromCollection(colAId, 'product-1');
      });

      const finalState = useFavoritesStore.getState();
      expect(finalState.favorites).toHaveLength(1);
      expect(finalState.favorites[0].id).toBe('product-2');
      expect(finalState.collections.find(c => c.id === colAId)?.productIds).not.toContain('product-1');
      expect(finalState.collections.find(c => c.id === colBId)?.productIds).toContain('product-1');
    });
  });
});
