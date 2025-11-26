import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { ProductCard } from '../ProductCard';
import type { Product } from '@/types';

const mockProduct: Product = {
    id: '1',
    tiktokId: 'prod_001',
    title: 'Test Product',
    description: 'Test description',
    price: 99.90,
    originalPrice: 149.90,
    currency: 'BRL',
    category: 'Electronics',
    subcategory: 'Audio',
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
    isOnSale: true,
    inStock: true,
    collectedAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
};

describe('ProductCard', () => {
    it('renders product information correctly', () => {
        const mockOnFavorite = vi.fn();

        render(
            <BrowserRouter>
                <ProductCard
                    product={mockProduct}
                    onFavorite={mockOnFavorite}
                    isFavorite={false}
                />
            </BrowserRouter>
        );

        expect(screen.getByText('Test Product')).toBeInTheDocument();
        expect(screen.getByText('R$ 99,90')).toBeInTheDocument();
        expect(screen.getByText('Electronics')).toBeInTheDocument();
    });

    it('shows trending badge when product is trending', () => {
        const mockOnFavorite = vi.fn();

        render(
            <BrowserRouter>
                <ProductCard
                    product={mockProduct}
                    onFavorite={mockOnFavorite}
                    isFavorite={false}
                />
            </BrowserRouter>
        );

        expect(screen.getByText('Em Alta')).toBeInTheDocument();
    });

    it('shows discount badge when product is on sale', () => {
        const mockOnFavorite = vi.fn();

        render(
            <BrowserRouter>
                <ProductCard
                    product={mockProduct}
                    onFavorite={mockOnFavorite}
                    isFavorite={false}
                />
            </BrowserRouter>
        );

        expect(screen.getByText(/-\d+%/)).toBeInTheDocument();
    });

    it('calls onFavorite when favorite button is clicked', async () => {
        const mockOnFavorite = vi.fn();
        const user = userEvent.setup();

        render(
            <BrowserRouter>
                <ProductCard
                    product={mockProduct}
                    onFavorite={mockOnFavorite}
                    isFavorite={false}
                />
            </BrowserRouter>
        );

        // Find button by its position (right side of image container)
        const buttons = screen.getAllByRole('button');
        const favoriteButton = buttons.find(btn =>
            btn.className.includes('absolute') && btn.className.includes('right-2')
        );

        expect(favoriteButton).toBeDefined();
        await user.click(favoriteButton!);

        expect(mockOnFavorite).toHaveBeenCalledWith(mockProduct);
    });
});
