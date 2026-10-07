import { ref, computed, type Ref } from 'vue';
import catalogApi from '../../../catalog/api';
import type { Product } from '../../../../types/api';

/**
 * Composable for managing Customer Erro carton serial numbers.
 * Per ADR 0006, Customer Erro strictly mandates automatic, monotonic serial numbers.
 * Manual sequence editing and toggling are completely removed.
 */
export function useErroSerialNumber(selectedProduct: Ref<Product | null>) {
  const isAutoSN = ref<boolean>(true);
  const autoSequence = ref<number>(1);
  const currentYYMM = ref<string>('');
  const nextCartonSN = ref<string>('');

  const fetchNextSN = async () => {
    if (!selectedProduct.value) return;
    try {
      const res = await catalogApi.getNextSN(selectedProduct.value.id);
      if (res?.data) {
        autoSequence.value = res.data.next_seq || 1;
        currentYYMM.value = res.data.yymm || '';
        nextCartonSN.value = res.data.next_sn || '';
      }
    } catch (err) {
      console.warn('Could not fetch next S/N sequence:', err);
    }
  };

  const currentSNPreview = computed<string>(() => {
    if (!selectedProduct.value) return '-';
    if ((selectedProduct.value.template_type === 'erro_04' || selectedProduct.value.template_type === 'erro_05') && nextCartonSN.value) {
      return nextCartonSN.value;
    }
    if (selectedProduct.value.template_type === 'erro_05') {
      const prefix = selectedProduct.value.pkg_prefix || 'MC220TW1';
      const now = new Date();
      const yy = String(now.getFullYear()).slice(-2);
      const d = new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()));
      const dayNum = d.getUTCDay() || 7;
      d.setUTCDate(d.getUTCDate() + 4 - dayNum);
      const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
      const weekNo = Math.ceil((((d.getTime() - yearStart.getTime()) / 86400000) + 1) / 7);
      const ww = String(weekNo).padStart(2, '0');
      const seqStr = String(autoSequence.value).padStart(5, '0');
      return `${prefix}2${yy}${ww}${seqStr}`;
    }
    if (selectedProduct.value.template_type === 'erro_03') {
      const supplierCode = selectedProduct.value.pkg_prefix || '1012665';
      const now = new Date();
      const yy = String(now.getFullYear()).slice(-2);
      const mm = String(now.getMonth() + 1).padStart(2, '0');
      const dd = String(now.getDate()).padStart(2, '0');
      const seqStr = String(autoSequence.value).padStart(4, '0');
      return `${supplierCode}${yy}${mm}${dd}${seqStr}`;
    }
    if (selectedProduct.value.template_type === 'erro_02') {
      const prefix = selectedProduct.value.pkg_prefix || '37033907';
      const seqStr = String(autoSequence.value).padStart(7, '0');
      return `(00) 0 ${prefix} ${seqStr}`;
    }
    const prefix = selectedProduct.value.pkg_prefix || 'VHK0010237';
    let yymm = currentYYMM.value;
    if (!yymm || yymm.length !== 4) {
      const now = new Date();
      const yy = String(now.getFullYear()).slice(-2);
      const mm = String(now.getMonth() + 1).padStart(2, '0');
      yymm = `${yy}${mm}`;
    }
    return `${prefix}${yymm}${String(autoSequence.value).padStart(6, '0')}`;
  });

  const advanceSequence = () => {
    autoSequence.value += 1;
    nextCartonSN.value = '';
  };

  return {
    isAutoSN,
    autoSequence,
    currentYYMM,
    nextCartonSN,
    currentSNPreview,
    fetchNextSN,
    advanceSequence,
  };
}
