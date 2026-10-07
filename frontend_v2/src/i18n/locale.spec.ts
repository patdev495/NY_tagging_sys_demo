import { describe, expect, it } from 'vitest';
import { displayLocale, formatNumber, normalizeLocale } from './locale';

describe('locale helpers', () => {
  it('accepts supported locales and safely defaults invalid values to Vietnamese', () => {
    expect(normalizeLocale('en')).toBe('en');
    expect(normalizeLocale('vi')).toBe('vi');
    expect(normalizeLocale('fr')).toBe('vi');
    expect(normalizeLocale(undefined)).toBe('vi');
  });

  it('formats numbers using selected display locale only', () => {
    expect(displayLocale('vi')).toBe('vi-VN');
    expect(displayLocale('en')).toBe('en-US');
    expect(formatNumber(1234.5, 'vi')).toBe('1.234,5');
    expect(formatNumber(1234.5, 'en')).toBe('1,234.5');
  });
});
