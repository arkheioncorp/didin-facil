/**
 * @fileoverview Utils Tests - 100% Coverage
 * @description Testes completos para funções utilitárias
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  cn,
  formatCurrency,
  formatNumber,
  formatPercentage,
  truncateText,
  generateId,
  debounce,
  sleep,
} from '@/lib/utils';

describe('Utils', () => {
  describe('cn() - Class Name Merger', () => {
    it('should merge class names', () => {
      const result = cn('class1', 'class2');
      expect(result).toBe('class1 class2');
    });

    it('should handle conditional classes', () => {
      const result = cn('base', true && 'conditional', false && 'hidden');
      expect(result).toBe('base conditional');
    });

    it('should merge Tailwind classes correctly', () => {
      const result = cn('px-4 py-2', 'px-6');
      expect(result).toBe('py-2 px-6');
    });

    it('should handle arrays', () => {
      const result = cn(['class1', 'class2']);
      expect(result).toBe('class1 class2');
    });

    it('should handle objects', () => {
      const result = cn({ 'class1': true, 'class2': false });
      expect(result).toBe('class1');
    });

    it('should handle empty inputs', () => {
      const result = cn();
      expect(result).toBe('');
    });

    it('should handle undefined values', () => {
      const result = cn('class1', undefined, 'class2');
      expect(result).toBe('class1 class2');
    });

    it('should handle null values', () => {
      const result = cn('class1', null, 'class2');
      expect(result).toBe('class1 class2');
    });

    it('should merge conflicting Tailwind utilities', () => {
      const result = cn('text-red-500', 'text-blue-500');
      expect(result).toBe('text-blue-500');
    });

    it('should handle complex combinations', () => {
      const result = cn(
        'base-class',
        ['array-class'],
        { 'object-class': true },
        true && 'conditional-class'
      );
      expect(result).toContain('base-class');
      expect(result).toContain('array-class');
      expect(result).toContain('object-class');
      expect(result).toContain('conditional-class');
    });
  });

  describe('formatCurrency()', () => {
    it('should format BRL currency by default', () => {
      const result = formatCurrency(99.99);
      expect(result).toMatch(/R\$\s*99,99/);
    });

    it('should format zero', () => {
      const result = formatCurrency(0);
      expect(result).toMatch(/R\$\s*0,00/);
    });

    it('should format large numbers', () => {
      const result = formatCurrency(1000000);
      expect(result).toMatch(/R\$\s*1\.000\.000,00/);
    });

    it('should format negative numbers', () => {
      const result = formatCurrency(-50);
      expect(result).toMatch(/-R\$\s*50,00/);
    });

    it('should handle custom currency', () => {
      const result = formatCurrency(100, 'USD');
      expect(result).toContain('$');
    });

    it('should format decimals correctly', () => {
      const result = formatCurrency(99.5);
      expect(result).toMatch(/R\$\s*99,50/);
    });

    it('should round long decimals', () => {
      const result = formatCurrency(99.999);
      expect(result).toMatch(/R\$\s*100,00/);
    });

    it('should handle very small numbers', () => {
      const result = formatCurrency(0.01);
      expect(result).toMatch(/R\$\s*0,01/);
    });

    it('should handle very large numbers', () => {
      const result = formatCurrency(999999999.99);
      expect(result).toMatch(/R\$\s*999\.999\.999,99/);
    });
  });

  describe('formatNumber()', () => {
    it('should format small numbers as-is', () => {
      const result = formatNumber(500);
      expect(result).toBe('500');
    });

    it('should format thousands with k suffix', () => {
      const result = formatNumber(1500);
      expect(result).toBe('1.5k');
    });

    it('should format millions with M suffix', () => {
      const result = formatNumber(1500000);
      expect(result).toBe('1.5M');
    });

    it('should handle exactly 1000', () => {
      const result = formatNumber(1000);
      expect(result).toBe('1.0k');
    });

    it('should handle exactly 1000000', () => {
      const result = formatNumber(1000000);
      expect(result).toBe('1.0M');
    });

    it('should handle zero', () => {
      const result = formatNumber(0);
      expect(result).toBe('0');
    });

    it('should format edge case 999', () => {
      const result = formatNumber(999);
      expect(result).toBe('999');
    });

    it('should format edge case 999999', () => {
      const result = formatNumber(999999);
      expect(result).toBe('1000.0k');
    });

    it('should handle large millions', () => {
      const result = formatNumber(50000000);
      expect(result).toBe('50.0M');
    });

    it('should handle decimals at boundaries', () => {
      const result = formatNumber(1001);
      expect(result).toBe('1.0k');
    });
  });

  describe('formatPercentage()', () => {
    it('should format integer percentage', () => {
      const result = formatPercentage(50);
      expect(result).toBe('50.0%');
    });

    it('should format decimal percentage', () => {
      const result = formatPercentage(33.333);
      expect(result).toBe('33.3%');
    });

    it('should format zero', () => {
      const result = formatPercentage(0);
      expect(result).toBe('0.0%');
    });

    it('should format 100%', () => {
      const result = formatPercentage(100);
      expect(result).toBe('100.0%');
    });

    it('should handle percentages over 100', () => {
      const result = formatPercentage(150);
      expect(result).toBe('150.0%');
    });

    it('should handle negative percentages', () => {
      const result = formatPercentage(-10);
      expect(result).toBe('-10.0%');
    });

    it('should round to one decimal place', () => {
      const result = formatPercentage(33.999);
      expect(result).toBe('34.0%');
    });

    it('should handle very small percentages', () => {
      const result = formatPercentage(0.1);
      expect(result).toBe('0.1%');
    });
  });

  describe('truncateText()', () => {
    it('should not truncate short text', () => {
      const result = truncateText('Hello', 10);
      expect(result).toBe('Hello');
    });

    it('should truncate long text', () => {
      const result = truncateText('Hello World', 5);
      expect(result).toBe('Hello...');
    });

    it('should handle exact length', () => {
      const result = truncateText('Hello', 5);
      expect(result).toBe('Hello');
    });

    it('should handle empty string', () => {
      const result = truncateText('', 10);
      expect(result).toBe('');
    });

    it('should handle zero max length', () => {
      const result = truncateText('Hello', 0);
      expect(result).toBe('...');
    });

    it('should add ellipsis', () => {
      const result = truncateText('This is a very long text', 10);
      expect(result).toMatch(/\.\.\.$/);
    });

    it('should truncate at correct position', () => {
      const result = truncateText('ABCDEFGHIJ', 5);
      expect(result).toBe('ABCDE...');
    });

    it('should handle unicode characters', () => {
      const result = truncateText('测试文本内容', 3);
      expect(result).toBe('测试文...');
    });

    it('should handle emojis', () => {
      const result = truncateText('🚀🎉🎊🎁', 2);
      expect(result).toBe('🚀🎉...');
    });
  });

  describe('generateId()', () => {
    it('should generate a string', () => {
      const result = generateId();
      expect(typeof result).toBe('string');
    });

    it('should generate unique IDs', () => {
      const ids = new Set<string>();
      for (let i = 0; i < 1000; i++) {
        ids.add(generateId());
      }
      expect(ids.size).toBe(1000);
    });

    it('should generate alphanumeric IDs', () => {
      const result = generateId();
      expect(result).toMatch(/^[a-z0-9]+$/);
    });

    it('should generate IDs with expected length', () => {
      const result = generateId();
      // substring(2, 15) = 13 characters max
      expect(result.length).toBeLessThanOrEqual(13);
      expect(result.length).toBeGreaterThan(0);
    });

    it('should not contain special characters', () => {
      for (let i = 0; i < 100; i++) {
        const id = generateId();
        expect(id).not.toMatch(/[^a-z0-9]/);
      }
    });
  });

  describe('debounce()', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('should debounce function calls', () => {
      const fn = vi.fn();
      const debouncedFn = debounce(fn, 100);

      debouncedFn();
      debouncedFn();
      debouncedFn();

      expect(fn).not.toHaveBeenCalled();

      vi.advanceTimersByTime(100);

      expect(fn).toHaveBeenCalledTimes(1);
    });

    it('should pass arguments to debounced function', () => {
      const fn = vi.fn();
      const debouncedFn = debounce(fn, 100);

      debouncedFn('arg1', 'arg2');

      vi.advanceTimersByTime(100);

      expect(fn).toHaveBeenCalledWith('arg1', 'arg2');
    });

    it('should use last arguments when called multiple times', () => {
      const fn = vi.fn();
      const debouncedFn = debounce(fn, 100);

      debouncedFn('first');
      debouncedFn('second');
      debouncedFn('third');

      vi.advanceTimersByTime(100);

      expect(fn).toHaveBeenCalledWith('third');
    });

    it('should reset timer on each call', () => {
      const fn = vi.fn();
      const debouncedFn = debounce(fn, 100);

      debouncedFn();
      vi.advanceTimersByTime(50);
      debouncedFn();
      vi.advanceTimersByTime(50);
      debouncedFn();
      vi.advanceTimersByTime(50);

      expect(fn).not.toHaveBeenCalled();

      vi.advanceTimersByTime(50);

      expect(fn).toHaveBeenCalledTimes(1);
    });

    it('should handle zero delay', () => {
      const fn = vi.fn();
      const debouncedFn = debounce(fn, 0);

      debouncedFn();

      vi.advanceTimersByTime(0);

      expect(fn).toHaveBeenCalledTimes(1);
    });

    it('should handle long delays', () => {
      const fn = vi.fn();
      const debouncedFn = debounce(fn, 10000);

      debouncedFn();

      vi.advanceTimersByTime(5000);
      expect(fn).not.toHaveBeenCalled();

      vi.advanceTimersByTime(5000);
      expect(fn).toHaveBeenCalledTimes(1);
    });

    it('should allow multiple independent debounced functions', () => {
      const fn1 = vi.fn();
      const fn2 = vi.fn();
      const debouncedFn1 = debounce(fn1, 100);
      const debouncedFn2 = debounce(fn2, 200);

      debouncedFn1();
      debouncedFn2();

      vi.advanceTimersByTime(100);

      expect(fn1).toHaveBeenCalledTimes(1);
      expect(fn2).not.toHaveBeenCalled();

      vi.advanceTimersByTime(100);

      expect(fn2).toHaveBeenCalledTimes(1);
    });
  });

  describe('sleep()', () => {
    beforeEach(() => {
      vi.useFakeTimers();
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('should return a promise', () => {
      const result = sleep(100);
      expect(result).toBeInstanceOf(Promise);
    });

    it('should resolve after specified time', async () => {
      const resolved = vi.fn();
      
      sleep(100).then(resolved);

      expect(resolved).not.toHaveBeenCalled();

      await vi.advanceTimersByTimeAsync(100);

      expect(resolved).toHaveBeenCalled();
    });

    it('should resolve with undefined', async () => {
      const promise = sleep(100);
      
      vi.advanceTimersByTime(100);
      
      const result = await promise;
      expect(result).toBeUndefined();
    });

    it('should handle zero delay', async () => {
      const resolved = vi.fn();
      
      sleep(0).then(resolved);

      await vi.advanceTimersByTimeAsync(0);

      expect(resolved).toHaveBeenCalled();
    });

    it('should handle long delays', async () => {
      const resolved = vi.fn();
      
      sleep(60000).then(resolved);

      await vi.advanceTimersByTimeAsync(30000);
      expect(resolved).not.toHaveBeenCalled();

      await vi.advanceTimersByTimeAsync(30000);
      expect(resolved).toHaveBeenCalled();
    });

    it('should be awaitable', async () => {
      let completed = false;
      
      const testAsync = async () => {
        await sleep(100);
        completed = true;
      };

      const promise = testAsync();

      expect(completed).toBe(false);

      await vi.advanceTimersByTimeAsync(100);
      await promise;

      expect(completed).toBe(true);
    });
  });
});
