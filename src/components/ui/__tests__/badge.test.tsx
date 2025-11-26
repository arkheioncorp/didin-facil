import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Badge } from '../badge';

describe('Badge', () => {
    it('renders children correctly', () => {
        render(<Badge>New</Badge>);
        expect(screen.getByText('New')).toBeInTheDocument();
    });

    it('applies default variant', () => {
        const { container } = render(<Badge>Default</Badge>);
        const badge = container.firstChild as HTMLElement;
        expect(badge.className).toContain('bg-primary');
    });

    it('applies secondary variant', () => {
        const { container } = render(<Badge variant="secondary">Secondary</Badge>);
        const badge = container.firstChild as HTMLElement;
        expect(badge.className).toContain('bg-secondary');
    });

    it('applies destructive variant', () => {
        const { container } = render(<Badge variant="destructive">Error</Badge>);
        const badge = container.firstChild as HTMLElement;
        expect(badge.className).toContain('bg-destructive');
    });

    it('applies outline variant', () => {
        const { container } = render(<Badge variant="outline">Outline</Badge>);
        const badge = container.firstChild as HTMLElement;
        expect(badge.className).toContain('border');
    });

    it('applies custom className', () => {
        const { container } = render(<Badge className="custom">Custom</Badge>);
        const badge = container.firstChild as HTMLElement;
        expect(badge.className).toContain('custom');
    });
});
