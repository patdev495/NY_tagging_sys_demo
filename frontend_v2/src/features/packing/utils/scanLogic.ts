/**
 * Core scan validation logic — extracted for testability.
 * These pure functions mirror the validation in UIPackingPage.vue.
 */

export interface InvalidScan {
  sn: string;
  time: string;
  reason: string;
  type: string;
}

export interface OverflowScan {
  sn: string;
  time: string;
  reason: string;
}

export interface ScanValidationContext {
  jobOrder: string;
  scannedItems: string[];
  packedQty: number;
  snPattern: string;
  isProcessing: boolean;
  awaitingNext: boolean;
  hasLockdownErrors: boolean;
}

export type ScanResult =
  | { ok: true; sn: string }
  | { ok: false; reason: string; type: 'no_job' | 'lockdown' | 'pattern' | 'duplicate' | 'overflow' | 'busy' };

/**
 * Validate a single scan against the current packing session state.
 */
export function validateScan(sn: string, ctx: ScanValidationContext): ScanResult {
  if (!sn) return { ok: false, reason: 'Empty scan', type: 'pattern' };

  // If awaiting next carton, reject all scans until next carton is activated
  if (ctx.awaitingNext) {
    return { ok: false, reason: 'Awaiting next carton', type: 'lockdown' };
  }

  // If processing
  if (ctx.isProcessing) {
    if (ctx.scannedItems.length >= ctx.packedQty) {
      return { ok: false, reason: 'Box Full', type: 'overflow' };
    }
    return { ok: false, reason: 'Processing', type: 'busy' };
  }

  // Must have job order
  if (!ctx.jobOrder) return { ok: false, reason: 'No job order', type: 'no_job' };

  // Station lockdown (previous unresolved errors)
  if (ctx.hasLockdownErrors) {
    return { ok: false, reason: 'Station locked — clear errors first', type: 'lockdown' };
  }

  // Prefix pattern check
  if (ctx.snPattern && !sn.startsWith(ctx.snPattern)) {
    return { ok: false, reason: 'Prefix mismatch', type: 'pattern' };
  }

  // Duplicate check
  if (ctx.scannedItems.includes(sn)) {
    return { ok: false, reason: 'Duplicate S/N', type: 'duplicate' };
  }

  // Over capacity
  if (ctx.scannedItems.length >= ctx.packedQty) {
    return { ok: false, reason: 'Box Full', type: 'overflow' };
  }

  return { ok: true, sn };
}

/**
 * Split raw scanner input into individual S/N strings.
 * Handles newlines, tabs, commas, and consecutive separators.
 */
export function splitBulkInput(raw: string): string[] {
  return raw.split(/\s*[\n\r\t,]+\s*/).map(s => s.trim()).filter(s => s.length > 0);
}

/**
 * Generate S/N preview string.
 */
export function generateSNPreview(
  startPart: string,
  middlePart: string,
  yymm: string,
  seq: number | string
): string {
  const prefix = `${startPart}${yymm}${middlePart}`;
  return `${prefix}${String(seq).padStart(5, '0')}`;
}
