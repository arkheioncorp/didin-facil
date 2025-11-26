import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from '../card';

describe('Card Components', () => {
    describe('Card', () => {
        it('renders children correctly', () => {
            render(<Card>Test Card</Card>);
            expect(screen.getByText('Test Card')).toBeInTheDocument();
        });

        it('applies custom className', () => {
            const { container } = render(<Card className="custom-class">Content</Card>);
            const card = container.firstChild as HTMLElement;
            expect(card.className).toContain('custom-class');
        });
    });

    describe('CardHeader', () => {
        it('renders header content', () => {
            render(<CardHeader>Header Content</CardHeader>);
            expect(screen.getByText('Header Content')).toBeInTheDocument();
        });
    });

    describe('CardTitle', () => {
        it('renders title as h3 by default', () => {
            render(<CardTitle>Card Title</CardTitle>);
            const title = screen.getByText('Card Title');
            expect(title.tagName).toBe('H3');
        });
    });

    describe('CardDescription', () => {
        it('renders description correctly', () => {
            render(<CardDescription>Card Description</CardDescription>);
            expect(screen.getByText('Card Description')).toBeInTheDocument();
        });
    });

    describe('CardContent', () => {
        it('renders content correctly', () => {
            render(<CardContent>Card Content</CardContent>);
            expect(screen.getByText('Card Content')).toBeInTheDocument();
        });
    });

    describe('CardFooter', () => {
        it('renders footer correctly', () => {
            render(<CardFooter>Card Footer</CardFooter>);
            expect(screen.getByText('Card Footer')).toBeInTheDocument();
        });
    });

    describe('Complete Card', () => {
        it('renders a complete card with all sections', () => {
            render(
                <Card>
                    <CardHeader>
                        <CardTitle>Test Title</CardTitle>
                        <CardDescription>Test Description</CardDescription>
                    </CardHeader>
                    <CardContent>Test Content</CardContent>
                    <CardFooter>Test Footer</CardFooter>
                </Card>
            );

            expect(screen.getByText('Test Title')).toBeInTheDocument();
            expect(screen.getByText('Test Description')).toBeInTheDocument();
            expect(screen.getByText('Test Content')).toBeInTheDocument();
            expect(screen.getByText('Test Footer')).toBeInTheDocument();
        });
    });
});
