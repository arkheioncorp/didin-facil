import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Button } from '../button';

describe('Button', () => {
    it('renders children correctly', () => {
        render(<Button>Click me</Button>);
        expect(screen.getByText('Click me')).toBeInTheDocument();
    });

    it('applies variant prop correctly', () => {
        const { container } = render(<Button variant="destructive">Delete</Button>);
        const button = container.querySelector('button');
        expect(button?.className).toContain('bg-destructive');
    });

    it('applies size prop correctly', () => {
        const { container } = render(<Button size="lg">Large</Button>);
        const button = container.querySelector('button');
        expect(button?.className).toContain('h-11');
    });

    it('handles onClick events', async () => {
        const handleClick = vi.fn();
        const user = userEvent.setup();

        render(<Button onClick={handleClick}>Click</Button>);
        await user.click(screen.getByText('Click'));

        expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('renders as disabled when disabled prop is true', () => {
        render(<Button disabled>Disabled</Button>);
        const button = screen.getByText('Disabled');
        expect(button).toBeDisabled();
    });

    it('renders with asChild prop', () => {
        render(
            <Button asChild>
                <a href="/test">Link Button</a>
            </Button>
        );
        expect(screen.getByText('Link Button').tagName).toBe('A');
    });
});
