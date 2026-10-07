import { ref } from 'vue';
import type { Product } from '../../../types/api';

interface InvalidScan {
  sn: string;
  time: string;
  reason: string;
}

interface ScanResult {
  success: boolean;
  error?: string;
}

export function useScanLogic() {
  const scannedItems = ref<string[]>([]);
  const scanBuffer = ref<string>('');
  const invalidScans = ref<InvalidScan[]>([]);

  const validateAndAddScan = (sn: string, currentProduct: Product, snPattern: string): ScanResult => {
    if (!sn) return { success: false, error: 'Empty scan' };

    // Duplicate check in current batch
    if (scannedItems.value.includes(sn)) {
      invalidScans.value.unshift({ sn, time: new Date().toLocaleTimeString(), reason: 'DUPLICATE IN BOX' });
      if (invalidScans.value.length > 5) invalidScans.value.pop();
      return { success: false, error: 'Duplicate S/N' };
    }

    // Pattern length check based on product
    const isVn = currentProduct.start_part === 'VN';
    const isCn = currentProduct.start_part === 'CN';
    const expectedLength = isVn ? 22 : (isCn ? 20 : null);
    
    if (expectedLength && sn.length !== expectedLength) {
      invalidScans.value.unshift({ 
        sn, 
        time: new Date().toLocaleTimeString(), 
        reason: `INVALID LENGTH (Expected ${expectedLength}, got ${sn.length})` 
      });
      if (invalidScans.value.length > 5) invalidScans.value.pop();
      return { success: false, error: 'Invalid Length' };
    }

    // Prefix pattern check
    if (snPattern && !sn.startsWith(snPattern)) {
      invalidScans.value.unshift({ 
        sn, 
        time: new Date().toLocaleTimeString(), 
        reason: `PATTERN MISMATCH (Expected: ${snPattern})` 
      });
      if (invalidScans.value.length > 5) invalidScans.value.pop();
      return { success: false, error: 'Pattern Mismatch' };
    }

    // Valid scan
    scannedItems.value.push(sn);
    return { success: true };
  };

  const resetScan = () => {
    scannedItems.value = [];
    scanBuffer.value = '';
    invalidScans.value = [];
  };

  return {
    scannedItems,
    scanBuffer,
    invalidScans,
    validateAndAddScan,
    resetScan
  };
}
