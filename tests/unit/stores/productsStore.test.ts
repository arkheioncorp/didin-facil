/**
 * Products Store Unit Tests
 * Tests for Zustand products store
 */
import { describe, it, expect, beforeEach } from "vitest";
import { act } from "@testing-library/react";
import { useProductsStore } from "@/stores/productsStore";
import type { Product } from "@/types";

// Mock product data
const createMockProduct = (id: string, overrides?: Partial<Product>): Product => ({
  id,
  tiktokId: `tiktok-${id}`,
  title: `Product ${id}`,
  description: `Description for product ${id}`,
  price: 99.90,
  originalPrice: 149.90,
  currency: "BRL",
  category: "electronics",
  subcategory: "audio",
  sellerName: "Test Seller",
  sellerRating: 4.5,
  productRating: 4.8,
  reviewsCount: 100,
  salesCount: 500,
  sales7d: 50,
  sales30d: 200,
  commissionRate: 10,
  imageUrl: `https://example.com/product-${id}.jpg`,
  images: [`https://example.com/product-${id}-1.jpg`],
  videoUrl: null,
  productUrl: `https://tiktok.com/product/${id}`,
  affiliateUrl: null,
  hasFreeShipping: true,
  isTrending: true,
  isOnSale: true,
  inStock: true,
  collectedAt: "2024-11-20T10:00:00Z",
  updatedAt: "2024-11-25T10:00:00Z",
  ...overrides,
});

const mockProducts: Product[] = [
  createMockProduct("1"),
  createMockProduct("2"),
  createMockProduct("3"),
];

describe("useProductsStore", () => {
  // Reset store before each test
  beforeEach(() => {
    const { reset } = useProductsStore.getState();
    act(() => {
      reset();
    });
  });

  describe("Initial State", () => {
    it("should have correct initial state", () => {
      const state = useProductsStore.getState();

      expect(state.products).toEqual([]);
      expect(state.selectedProduct).toBeNull();
      expect(state.total).toBe(0);
      expect(state.page).toBe(1);
      expect(state.hasMore).toBe(true);
      expect(state.isLoading).toBe(false);
      expect(state.isLoadingMore).toBe(false);
      expect(state.error).toBeNull();
    });
  });

  describe("setProducts", () => {
    it("should set products with pagination info", () => {
      const { setProducts } = useProductsStore.getState();

      act(() => {
        setProducts(mockProducts, 100, true);
      });

      const state = useProductsStore.getState();
      expect(state.products).toEqual(mockProducts);
      expect(state.total).toBe(100);
      expect(state.hasMore).toBe(true);
      expect(state.page).toBe(1); // Resets to page 1
    });

    it("should set hasMore to false when no more products", () => {
      const { setProducts } = useProductsStore.getState();

      act(() => {
        setProducts(mockProducts, 3, false);
      });

      const state = useProductsStore.getState();
      expect(state.hasMore).toBe(false);
    });

    it("should replace existing products", () => {
      const { setProducts } = useProductsStore.getState();

      // Set initial products
      act(() => {
        setProducts(mockProducts, 3, false);
      });

      // Set new products
      const newProducts = [createMockProduct("4"), createMockProduct("5")];
      act(() => {
        setProducts(newProducts, 2, false);
      });

      const state = useProductsStore.getState();
      expect(state.products).toEqual(newProducts);
      expect(state.products.length).toBe(2);
    });
  });

  describe("appendProducts", () => {
    it("should append products to existing list", () => {
      const { setProducts, appendProducts } = useProductsStore.getState();

      // Set initial products
      act(() => {
        setProducts(mockProducts, 100, true);
      });

      // Append more products
      const moreProducts = [createMockProduct("4"), createMockProduct("5")];
      act(() => {
        appendProducts(moreProducts);
      });

      const state = useProductsStore.getState();
      expect(state.products.length).toBe(5);
      expect(state.products[3].id).toBe("4");
      expect(state.products[4].id).toBe("5");
    });

    it("should increment page number when appending", () => {
      const { setProducts, appendProducts } = useProductsStore.getState();

      act(() => {
        setProducts(mockProducts, 100, true);
      });

      expect(useProductsStore.getState().page).toBe(1);

      act(() => {
        appendProducts([createMockProduct("4")]);
      });

      expect(useProductsStore.getState().page).toBe(2);
    });

    it("should handle appending to empty list", () => {
      const { appendProducts } = useProductsStore.getState();

      act(() => {
        appendProducts(mockProducts);
      });

      const state = useProductsStore.getState();
      expect(state.products).toEqual(mockProducts);
      expect(state.page).toBe(2); // Incremented from 1
    });
  });

  describe("setSelectedProduct", () => {
    it("should set selected product", () => {
      const { setSelectedProduct } = useProductsStore.getState();
      const product = createMockProduct("1");

      act(() => {
        setSelectedProduct(product);
      });

      expect(useProductsStore.getState().selectedProduct).toEqual(product);
    });

    it("should clear selected product when set to null", () => {
      const { setSelectedProduct } = useProductsStore.getState();
      const product = createMockProduct("1");

      act(() => {
        setSelectedProduct(product);
      });

      act(() => {
        setSelectedProduct(null);
      });

      expect(useProductsStore.getState().selectedProduct).toBeNull();
    });
  });

  describe("setPage", () => {
    it("should set page number", () => {
      const { setPage } = useProductsStore.getState();

      act(() => {
        setPage(5);
      });

      expect(useProductsStore.getState().page).toBe(5);
    });

    it("should handle page 1", () => {
      const { setPage } = useProductsStore.getState();

      act(() => {
        setPage(10);
      });

      act(() => {
        setPage(1);
      });

      expect(useProductsStore.getState().page).toBe(1);
    });
  });

  describe("Loading States", () => {
    it("should set loading state", () => {
      const { setLoading } = useProductsStore.getState();

      act(() => {
        setLoading(true);
      });

      expect(useProductsStore.getState().isLoading).toBe(true);

      act(() => {
        setLoading(false);
      });

      expect(useProductsStore.getState().isLoading).toBe(false);
    });

    it("should set loading more state", () => {
      const { setLoadingMore } = useProductsStore.getState();

      act(() => {
        setLoadingMore(true);
      });

      expect(useProductsStore.getState().isLoadingMore).toBe(true);

      act(() => {
        setLoadingMore(false);
      });

      expect(useProductsStore.getState().isLoadingMore).toBe(false);
    });

    it("should allow both loading states simultaneously", () => {
      const { setLoading, setLoadingMore } = useProductsStore.getState();

      act(() => {
        setLoading(true);
        setLoadingMore(true);
      });

      const state = useProductsStore.getState();
      expect(state.isLoading).toBe(true);
      expect(state.isLoadingMore).toBe(true);
    });
  });

  describe("Error Handling", () => {
    it("should set error message", () => {
      const { setError } = useProductsStore.getState();

      act(() => {
        setError("Failed to load products");
      });

      expect(useProductsStore.getState().error).toBe("Failed to load products");
    });

    it("should clear error message", () => {
      const { setError } = useProductsStore.getState();

      act(() => {
        setError("Some error");
      });

      act(() => {
        setError(null);
      });

      expect(useProductsStore.getState().error).toBeNull();
    });
  });

  describe("reset", () => {
    it("should reset to initial state", () => {
      const {
        setProducts,
        setSelectedProduct,
        setLoading,
        setError,
        reset,
      } = useProductsStore.getState();

      // Modify state
      act(() => {
        setProducts(mockProducts, 100, false);
        setSelectedProduct(mockProducts[0]);
        setLoading(true);
        setError("Some error");
      });

      // Reset
      act(() => {
        reset();
      });

      const state = useProductsStore.getState();
      expect(state.products).toEqual([]);
      expect(state.selectedProduct).toBeNull();
      expect(state.total).toBe(0);
      expect(state.page).toBe(1);
      expect(state.hasMore).toBe(true);
      expect(state.isLoading).toBe(false);
      expect(state.isLoadingMore).toBe(false);
      expect(state.error).toBeNull();
    });
  });

  describe("Integration Scenarios", () => {
    it("should handle typical pagination flow", () => {
      const {
        setProducts,
        appendProducts,
        setLoading,
        setLoadingMore,
      } = useProductsStore.getState();

      // Initial load
      act(() => {
        setLoading(true);
      });

      expect(useProductsStore.getState().isLoading).toBe(true);

      act(() => {
        setProducts(mockProducts, 100, true);
        setLoading(false);
      });

      let state = useProductsStore.getState();
      expect(state.isLoading).toBe(false);
      expect(state.products.length).toBe(3);
      expect(state.page).toBe(1);

      // Load more
      act(() => {
        setLoadingMore(true);
      });

      const moreProducts = [
        createMockProduct("4"),
        createMockProduct("5"),
        createMockProduct("6"),
      ];

      act(() => {
        appendProducts(moreProducts);
        setLoadingMore(false);
      });

      state = useProductsStore.getState();
      expect(state.isLoadingMore).toBe(false);
      expect(state.products.length).toBe(6);
      expect(state.page).toBe(2);
    });

    it("should handle error during loading", () => {
      const { setLoading, setError } = useProductsStore.getState();

      act(() => {
        setLoading(true);
      });

      // Simulate error
      act(() => {
        setLoading(false);
        setError("Network error: Failed to fetch products");
      });

      const state = useProductsStore.getState();
      expect(state.isLoading).toBe(false);
      expect(state.error).toBe("Network error: Failed to fetch products");
      expect(state.products).toEqual([]); // Products should remain empty
    });

    it("should handle product selection flow", () => {
      const { setProducts, setSelectedProduct } = useProductsStore.getState();

      act(() => {
        setProducts(mockProducts, 3, false);
      });

      // Select a product
      act(() => {
        setSelectedProduct(mockProducts[1]);
      });

      expect(useProductsStore.getState().selectedProduct?.id).toBe("2");

      // Change selection
      act(() => {
        setSelectedProduct(mockProducts[0]);
      });

      expect(useProductsStore.getState().selectedProduct?.id).toBe("1");

      // Clear selection
      act(() => {
        setSelectedProduct(null);
      });

      expect(useProductsStore.getState().selectedProduct).toBeNull();
    });

    it("should handle refresh (re-fetch) scenario", () => {
      const { setProducts, setLoading, reset } = useProductsStore.getState();

      // Initial data
      act(() => {
        setProducts(mockProducts, 100, true);
      });

      expect(useProductsStore.getState().products.length).toBe(3);

      // Refresh - reset and reload
      act(() => {
        reset();
        setLoading(true);
      });

      expect(useProductsStore.getState().products.length).toBe(0);
      expect(useProductsStore.getState().isLoading).toBe(true);

      // New data arrives
      const freshProducts = [
        createMockProduct("10"),
        createMockProduct("20"),
      ];

      act(() => {
        setProducts(freshProducts, 50, true);
        setLoading(false);
      });

      const state = useProductsStore.getState();
      expect(state.products.length).toBe(2);
      expect(state.products[0].id).toBe("10");
    });
  });

  describe("Edge Cases", () => {
    it("should handle empty products array", () => {
      const { setProducts } = useProductsStore.getState();

      act(() => {
        setProducts([], 0, false);
      });

      const state = useProductsStore.getState();
      expect(state.products).toEqual([]);
      expect(state.total).toBe(0);
      expect(state.hasMore).toBe(false);
    });

    it("should handle large product counts", () => {
      const { setProducts } = useProductsStore.getState();

      act(() => {
        setProducts(mockProducts, 10000, true);
      });

      expect(useProductsStore.getState().total).toBe(10000);
    });

    it("should maintain product order", () => {
      const { setProducts } = useProductsStore.getState();

      const orderedProducts = [
        createMockProduct("a"),
        createMockProduct("b"),
        createMockProduct("c"),
      ];

      act(() => {
        setProducts(orderedProducts, 3, false);
      });

      const state = useProductsStore.getState();
      expect(state.products[0].id).toBe("a");
      expect(state.products[1].id).toBe("b");
      expect(state.products[2].id).toBe("c");
    });
  });
});
