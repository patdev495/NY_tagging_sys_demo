import { describe, it, expect } from 'vitest';
import { validateScan, splitBulkInput, generateSNPreview, type ScanValidationContext } from '../utils/scanLogic';

function makeCtx(overrides: Partial<ScanValidationContext> = {}): ScanValidationContext {
  return {
    jobOrder: 'JO-001',
    scannedItems: [],
    packedQty: 10,
    snPattern: '',
    isProcessing: false,
    awaitingNext: false,
    hasLockdownErrors: false,
    ...overrides,
  };
}

describe('validateScan', () => {
  it('accepts a valid scan', () => {
    const result = validateScan('SN001', makeCtx());
    expect(result.ok).toBe(true);
  });

  it('rejects empty scan', () => {
    const result = validateScan('', makeCtx());
    expect(result.ok).toBe(false);
  });

  it('rejects scan without job order', () => {
    const result = validateScan('SN001', makeCtx({ jobOrder: '' }));
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe('no_job');
  });

  it('rejects duplicate S/N', () => {
    const result = validateScan('SN001', makeCtx({ scannedItems: ['SN001'] }));
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe('duplicate');
  });

  it('rejects scan when prefix pattern does not match', () => {
    const result = validateScan('ABC123', makeCtx({ snPattern: 'XYZ' }));
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe('pattern');
  });

  it('accepts scan when prefix pattern matches', () => {
    const result = validateScan('XYZ123', makeCtx({ snPattern: 'XYZ' }));
    expect(result.ok).toBe(true);
  });

  it('rejects scan when box is full (overflow)', () => {
    const result = validateScan('SN011', makeCtx({
      scannedItems: Array.from({ length: 10 }, (_, i) => `SN${i}`),
      packedQty: 10,
    }));
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe('overflow');
  });

  it('rejects scan during lockdown', () => {
    const result = validateScan('SN001', makeCtx({ hasLockdownErrors: true }));
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe('lockdown');
  });

  it('rejects scan when processing', () => {
    const result = validateScan('SN001', makeCtx({ isProcessing: true }));
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe('busy');
  });

  it('rejects scan when awaiting next carton', () => {
    const result = validateScan('SN001', makeCtx({ awaitingNext: true }));
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe('lockdown');
  });

  it('returns overflow when processing and box is full', () => {
    const result = validateScan('SN001', makeCtx({
      isProcessing: true,
      scannedItems: Array.from({ length: 10 }, (_, i) => `SN${i}`),
      packedQty: 10,
    }));
    expect(result.ok).toBe(false);
    if (!result.ok) expect(result.type).toBe('overflow');
  });
});

describe('splitBulkInput', () => {
  it('splits newline-separated input', () => {
    expect(splitBulkInput('SN001\nSN002\nSN003')).toEqual(['SN001', 'SN002', 'SN003']);
  });

  it('splits comma-separated input', () => {
    expect(splitBulkInput('SN001,SN002,SN003')).toEqual(['SN001', 'SN002', 'SN003']);
  });

  it('splits tab-separated input', () => {
    expect(splitBulkInput('SN001\tSN002\tSN003')).toEqual(['SN001', 'SN002', 'SN003']);
  });

  it('handles consecutive separators', () => {
    expect(splitBulkInput('SN001\n\n\nSN002')).toEqual(['SN001', 'SN002']);
  });

  it('trims whitespace around items', () => {
    expect(splitBulkInput(' SN001 , SN002 ')).toEqual(['SN001', 'SN002']);
  });

  it('returns empty array for empty input', () => {
    expect(splitBulkInput('')).toEqual([]);
  });

  it('returns empty array for whitespace-only input', () => {
    expect(splitBulkInput('   ')).toEqual([]);
  });

  it('preserves spaces within S/N values', () => {
    expect(splitBulkInput('SN 001\nSN 002')).toEqual(['SN 001', 'SN 002']);
  });
});

describe('generateSNPreview', () => {
  it('generates correct preview with all parts', () => {
    expect(generateSNPreview('VN', '11', '2605', 1)).toBe('VN260511' + '00001');
  });

  it('pads sequence to 5 digits', () => {
    expect(generateSNPreview('CN', '16', '2601', 42)).toBe('CN260116' + '00042');
  });

  it('handles string sequence input', () => {
    expect(generateSNPreview('VN', '11', '2605', '123')).toBe('VN260511' + '00123');
  });

  it('handles empty start/middle parts', () => {
    expect(generateSNPreview('', '', '2605', 1)).toBe('2605' + '00001');
  });
});
