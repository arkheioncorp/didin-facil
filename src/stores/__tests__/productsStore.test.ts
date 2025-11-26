import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useProductsStore } from '../productsStore';
import type { Product } from '@/types';

const mockProduct: Product = {
    id: '1',
    tiktokId: 'prod_001',
    title: 'Test Product',
    description: 'Test description',
    price: 99.90,
    originalPrice: null,
    currency: 'BRL',
    category: 'Electronics',
    subcategory: null,
    sellerName: 'Test Store',
    sellerRating: 4.8,
    productRating: 4.7,
    reviewsCount: 100,
    salesCount: 500,
    sales7d: 50,
    sales30d: 200,
    commissionRate: 15,
    imageUrl: 'https://example.com/image.jpg',
    images: [],
    videoUrl: null,
    productUrl: 'https://tiktok.com/product/1',
    affiliateUrl: null,
    hasFreeShipping: true,
    isTrending: true,
    isOnSale: false,
    inStock: true,
    collectedAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
};

describe('useProductsStore', () => {
    beforeEach(() => {
        const { result } = renderHook(() => useProductsStore());
        act(() => {
            result.current.reset();
        });
    });

    it('initializes with empty state', () => {
        const { result } = renderHook(() => useProductsStore());

        expect(result.current.products).toEqual([]);
        expect(result.current.selectedProduct).toBeNull();
        expect(result.current.total).toBe(0);
        expect(result.current.page).toBe(1);
        expect(result.current.isLoading).toBe(false);
    });

    it('sets products correctly', () => {
        const { result } = renderHook(() => useProductsStore());

        act(() => {
            result.current.setProducts([mockProduct], 1, false);
        });

        expect(result.current.products).toHaveLength(1);
        expect(result.current.products[0].id).toBe('1');
        expect(result.current.total).toBe(1);
        expect(result.current.hasMore).toBe(false);
    });

    it('appends products correctly', () => {
        const { result } = renderHook(() => useProductsStore());

        act(() => {
            result.current.setProducts([mockProduct], 1, true);
        });

        const secondProduct = { ...mockProduct, id: '2', tiktokId: 'prod_002' };

        act(() => {
            result.current.appendProducts([secondProduct]);
        });

        expect(result.current.products).toHaveLength(2);
        expect(result.current.page).toBe(2);
    });

    it('sets selected product', () => {
        const { result } = renderHook(() => useProductsStore());

        act(() => {
            result.current.setSelectedProduct(mockProduct);
        });

        expect(result.current.selectedProduct).toEqual(mockProduct);
    });

    it('sets loading state', () => {
        const { result } = renderHook(() => useProductsStore());

        act(() => {
            result.current.setLoading(true);
        });

        expect(result.current.isLoading).toBe(true);
    });

    it('resets to initial state', () => {
        const { result } = renderHook(() => useProductsStore());

        act(() => {
            result.current.setProducts([mockProduct], 1, false);
            result.current.setLoading(true);
        });

        act(() => {
            result.current.reset();
        });

        expect(result.current.products).toEqual([]);
        expect(result.current.isLoading).toBe(false);
        expect(result.current.total).toBe(0);
    });
});
