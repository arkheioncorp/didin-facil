/**
 * ProductCard Component Unit Tests
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "../../helpers/render";
import { ProductCard } from "@/components/product/ProductCard";
import type { Product } from "@/types";

// Mock product data
const createMockProduct = (overrides?: Partial<Product>): Product => ({
  id: "prod-1",
  tiktokId: "tiktok-1",
  title: "Fone de Ouvido Bluetooth Premium",
  description: "Fone sem fio com cancelamento de ruído",
  price: 199.90,
  originalPrice: 299.90,
  currency: "BRL",
  category: "electronics",
  subcategory: "audio",
  sellerName: "Test Seller",
  sellerRating: 4.5,
  productRating: 4.8,
  reviewsCount: 150,
  salesCount: 2500,
  sales7d: 350,
  sales30d: 1200,
  commissionRate: 10,
  imageUrl: "https://example.com/product.jpg",
  images: ["https://example.com/product-1.jpg"],
  videoUrl: null,
  productUrl: "https://tiktok.com/product/1",
  affiliateUrl: null,
  hasFreeShipping: true,
  isTrending: true,
  isOnSale: true,
  inStock: true,
  collectedAt: "2024-11-20T10:00:00Z",
  updatedAt: "2024-11-25T10:00:00Z",
  ...overrides,
});

describe("ProductCard", () => {
  let mockOnFavorite: ReturnType<typeof vi.fn>;
  let mockOnSelect: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    mockOnFavorite = vi.fn();
    mockOnSelect = vi.fn();
  });

  describe("Rendering", () => {
    it("should render product title", () => {
      const product = createMockProduct();
      render(<ProductCard product={product} />);

      expect(screen.getByText(product.title)).toBeInTheDocument();
    });

    it("should render product price", () => {
      const product = createMockProduct();
      render(<ProductCard product={product} />);

      // Price should be formatted as currency
      expect(screen.getByText(/R\$\s*199,90/)).toBeInTheDocument();
    });

    it("should render original price with strikethrough when discounted", () => {
      const product = createMockProduct({
        price: 199.90,
        originalPrice: 299.90,
      });
      render(<ProductCard product={product} />);

      expect(screen.getByText(/R\$\s*299,90/)).toBeInTheDocument();
    });

    it("should not render original price when not discounted", () => {
      const product = createMockProduct({ originalPrice: null });
      render(<ProductCard product={product} />);

      // Only current price should be visible
      const priceElements = screen.getAllByText(/R\$/);
      expect(priceElements.length).toBe(1);
    });

    it("should render product image", () => {
      const product = createMockProduct();
      render(<ProductCard product={product} />);

      const image = screen.getByRole("img");
      expect(image).toHaveAttribute("src", product.imageUrl);
      expect(image).toHaveAttribute("alt", product.title);
    });

    it("should render placeholder image when imageUrl is null", () => {
      const product = createMockProduct({ imageUrl: null });
      render(<ProductCard product={product} />);

      const image = screen.getByRole("img");
      expect(image).toHaveAttribute("src", expect.stringContaining("placehold"));
    });

    it("should render category badge", () => {
      const product = createMockProduct({ category: "electronics" });
      render(<ProductCard product={product} />);

      expect(screen.getByText("electronics")).toBeInTheDocument();
    });

    it("should render 'Sem categoria' when category is null", () => {
      const product = createMockProduct({ category: null });
      render(<ProductCard product={product} />);

      expect(screen.getByText("Sem categoria")).toBeInTheDocument();
    });

    it("should render product rating", () => {
      const product = createMockProduct({ productRating: 4.8 });
      render(<ProductCard product={product} />);

      expect(screen.getByText("4.8")).toBeInTheDocument();
    });

    it("should render N/A when rating is null", () => {
      const product = createMockProduct({ productRating: null });
      render(<ProductCard product={product} />);

      expect(screen.getByText("N/A")).toBeInTheDocument();
    });

    it("should render sales count", () => {
      const product = createMockProduct({ salesCount: 2500 });
      render(<ProductCard product={product} />);

      expect(screen.getByText(/2\.?5?.*vendas/i)).toBeInTheDocument();
    });

    it("should render reviews count", () => {
      const product = createMockProduct({ reviewsCount: 150 });
      render(<ProductCard product={product} />);

      expect(screen.getByText(/\(150\)/)).toBeInTheDocument();
    });
  });

  describe("Badges", () => {
    it("should render trending badge when product is trending", () => {
      const product = createMockProduct({ isTrending: true });
      render(<ProductCard product={product} />);

      expect(screen.getByText("Em Alta")).toBeInTheDocument();
    });

    it("should not render trending badge when product is not trending", () => {
      const product = createMockProduct({ isTrending: false });
      render(<ProductCard product={product} />);

      expect(screen.queryByText("Em Alta")).not.toBeInTheDocument();
    });

    it("should render discount badge when product has discount", () => {
      const product = createMockProduct({
        price: 199.90,
        originalPrice: 299.90,
      });
      render(<ProductCard product={product} />);

      // Should show approximately 33% discount
      expect(screen.getByText(/-33%/)).toBeInTheDocument();
    });

    it("should not render discount badge when no original price", () => {
      const product = createMockProduct({ originalPrice: null });
      render(<ProductCard product={product} />);

      expect(screen.queryByText(/-%/)).not.toBeInTheDocument();
    });

    it("should render free shipping badge when available", () => {
      const product = createMockProduct({ hasFreeShipping: true });
      render(<ProductCard product={product} />);

      expect(screen.getByText("Frete Grátis")).toBeInTheDocument();
    });

    it("should not render free shipping badge when not available", () => {
      const product = createMockProduct({ hasFreeShipping: false });
      render(<ProductCard product={product} />);

      expect(screen.queryByText("Frete Grátis")).not.toBeInTheDocument();
    });
  });

  describe("7-Day Sales", () => {
    it("should render 7-day sales when available", () => {
      const product = createMockProduct({ sales7d: 350 });
      render(<ProductCard product={product} />);

      expect(screen.getByText("Vendas 7d")).toBeInTheDocument();
      expect(screen.getByText(/\+350/)).toBeInTheDocument();
    });

    it("should not render 7-day sales section when sales7d is 0", () => {
      const product = createMockProduct({ sales7d: 0 });
      render(<ProductCard product={product} />);

      expect(screen.queryByText("Vendas 7d")).not.toBeInTheDocument();
    });
  });

  describe("Interactions", () => {
    it("should call onSelect when card is clicked", () => {
      const product = createMockProduct();
      render(<ProductCard product={product} onSelect={mockOnSelect} />);

      const card = screen.getByRole("img").closest(".cursor-pointer");
      if (card) {
        fireEvent.click(card);
      }

      expect(mockOnSelect).toHaveBeenCalledWith(product);
    });

    it("should call onFavorite when favorite button is clicked", () => {
      const product = createMockProduct();
      render(
        <ProductCard
          product={product}
          onFavorite={mockOnFavorite}
          isFavorite={false}
        />
      );

      const favoriteButton = screen.getByRole("button");
      fireEvent.click(favoriteButton);

      expect(mockOnFavorite).toHaveBeenCalledWith(product);
    });

    it("should not call onSelect when favorite button is clicked", () => {
      const product = createMockProduct();
      render(
        <ProductCard
          product={product}
          onSelect={mockOnSelect}
          onFavorite={mockOnFavorite}
        />
      );

      const favoriteButton = screen.getByRole("button");
      fireEvent.click(favoriteButton);

      expect(mockOnFavorite).toHaveBeenCalled();
      expect(mockOnSelect).not.toHaveBeenCalled();
    });

    it("should not render favorite button when onFavorite is not provided", () => {
      const product = createMockProduct();
      render(<ProductCard product={product} />);

      expect(screen.queryByRole("button")).not.toBeInTheDocument();
    });
  });

  describe("Favorite State", () => {
    it("should show filled heart icon when isFavorite is true", () => {
      const product = createMockProduct();
      render(
        <ProductCard
          product={product}
          onFavorite={mockOnFavorite}
          isFavorite={true}
        />
      );

      const button = screen.getByRole("button");
      const icon = button.querySelector("svg");
      expect(icon).toHaveClass("fill-tiktrend-primary");
    });

    it("should show empty heart icon when isFavorite is false", () => {
      const product = createMockProduct();
      render(
        <ProductCard
          product={product}
          onFavorite={mockOnFavorite}
          isFavorite={false}
        />
      );

      const button = screen.getByRole("button");
      const icon = button.querySelector("svg");
      expect(icon).not.toHaveClass("fill-tiktrend-primary");
    });
  });

  describe("Edge Cases", () => {
    it("should handle very long product titles", () => {
      const longTitle = "A".repeat(200);
      const product = createMockProduct({ title: longTitle });
      render(<ProductCard product={product} />);

      // Title should be truncated (line-clamp-2)
      const titleElement = screen.getByText(longTitle);
      expect(titleElement).toHaveClass("line-clamp-2");
    });

    it("should handle zero price", () => {
      const product = createMockProduct({ price: 0 });
      render(<ProductCard product={product} />);

      expect(screen.getByText(/R\$\s*0,00/)).toBeInTheDocument();
    });

    it("should handle very high prices", () => {
      const product = createMockProduct({ price: 999999.99 });
      render(<ProductCard product={product} />);

      // Should format with thousands separator
      expect(screen.getByText(/999\.999,99/)).toBeInTheDocument();
    });

    it("should handle zero reviews", () => {
      const product = createMockProduct({ reviewsCount: 0 });
      render(<ProductCard product={product} />);

      expect(screen.getByText("(0)")).toBeInTheDocument();
    });

    it("should handle missing optional callbacks", () => {
      const product = createMockProduct();
      
      // Should not throw when callbacks are not provided
      expect(() => {
        render(<ProductCard product={product} />);
      }).not.toThrow();
    });
  });

  describe("Accessibility", () => {
    it("should have alt text on product image", () => {
      const product = createMockProduct();
      render(<ProductCard product={product} />);

      const image = screen.getByRole("img");
      expect(image).toHaveAttribute("alt", product.title);
    });

    it("should use lazy loading for images", () => {
      const product = createMockProduct();
      render(<ProductCard product={product} />);

      const image = screen.getByRole("img");
      expect(image).toHaveAttribute("loading", "lazy");
    });
  });

  describe("Discount Calculation", () => {
    it("should calculate 50% discount correctly", () => {
      const product = createMockProduct({
        price: 100,
        originalPrice: 200,
      });
      render(<ProductCard product={product} />);

      expect(screen.getByText("-50%")).toBeInTheDocument();
    });

    it("should round discount to nearest integer", () => {
      const product = createMockProduct({
        price: 149.90,
        originalPrice: 199.90,
      });
      render(<ProductCard product={product} />);

      // 25% discount, rounded
      expect(screen.getByText(/-25%/)).toBeInTheDocument();
    });

    it("should not show 0% discount", () => {
      const product = createMockProduct({
        price: 199.90,
        originalPrice: 199.90,
      });
      render(<ProductCard product={product} />);

      expect(screen.queryByText("-0%")).not.toBeInTheDocument();
    });
  });
});
