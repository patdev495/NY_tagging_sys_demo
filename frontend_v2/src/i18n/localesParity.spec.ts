import { describe, expect, it } from 'vitest';
import en from './locales/en';
import vi from './locales/vi';

function flatten(value: Record<string, unknown>, prefix = ''): string[] {
  return Object.entries(value).flatMap(([key, item]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    return item && typeof item === 'object' ? flatten(item as Record<string, unknown>, path) : [path];
  });
}

describe('locale catalogs', () => {
  it('keeps Vietnamese and English keys exactly in sync', () => {
    expect(flatten(en).sort()).toEqual(flatten(vi).sort());
  });
});
