import { ref, computed, watch, type Ref } from 'vue';
import type { Product, JobOrderSlot } from '../../../types/api';

export interface UseJobOrderSlotsOptions {
  system: any;
  currentProduct: Ref<Product | null>;
  customYYMM: Ref<string>;
  customSN: Ref<string>;
  suggestedSNPreview: Ref<string>;
  isSNManual: Ref<boolean>;
  scannedItems: Ref<string[]>;
  focusScan: () => void;
  confirmDiscardMsg?: string;
}

export function useJobOrderSlots(options: UseJobOrderSlotsOptions) {
  const jobOrderSlots = ref<JobOrderSlot[]>([]);
  const cartonNumberStr = ref<string>('');
  const selectedSlotId = ref<number | null>(null);
  const hasCartonNumberError = ref<boolean>(false);
  const cartonNumberErrorText = ref<string>('');

  const scannedCartonsCount = computed(() => jobOrderSlots.value.filter(s => s.status === 'SCANNED').length);

  const getActiveYYMM = () => options.customYYMM.value && options.customYYMM.value.length === 4
    ? options.customYYMM.value
    : `${String(new Date().getFullYear()).slice(-2)}${String(new Date().getMonth() + 1).padStart(2, '0')}`;

  const cartonNumberRange = computed(() => {
    if (jobOrderSlots.value.length === 0) return '';
    let minSeq = Infinity, maxSeq = -Infinity;
    for (const slot of jobOrderSlots.value) {
      const seqMatch = slot.carton_sn.match(/\d{5}$/);
      if (seqMatch) {
        const seq = parseInt(seqMatch[0]);
        if (seq < minSeq) minSeq = seq;
        if (seq > maxSeq) maxSeq = seq;
      }
    }
    return minSeq === Infinity || maxSeq === -Infinity ? '' : `${minSeq} -> ${maxSeq}`;
  });

  const selectSlot = (slot: JobOrderSlot, confirmDiscard = true) => {
    hasCartonNumberError.value = false;
    cartonNumberErrorText.value = '';
    if (slot.status === 'SCANNED') return;
    if (confirmDiscard && options.scannedItems.value.length > 0 && selectedSlotId.value !== slot.id) {
      if (options.confirmDiscardMsg && !confirm(options.confirmDiscardMsg)) return;
    }
    selectedSlotId.value = slot.id;
    const sn = slot.carton_sn;
    const seqMatch = sn.match(/\d{5}$/);
    if (seqMatch) {
      const seqNum = parseInt(seqMatch[0]);
      cartonNumberStr.value = seqNum.toString();
      options.customSN.value = seqNum.toString();
    } else {
      cartonNumberStr.value = '';
      options.customSN.value = '';
      options.suggestedSNPreview.value = '';
    }
    if (sn.length >= 6) options.customYYMM.value = sn.slice(2, 6);
    options.isSNManual.value = true;
    options.scannedItems.value = [];
    options.focusScan();
  };

  const handleCartonNumberSubmit = () => {
    const num = parseInt(cartonNumberStr.value);
    if (isNaN(num)) {
      hasCartonNumberError.value = true;
      cartonNumberErrorText.value = 'Vui lòng nhập số sê-ri thùng hợp lệ!';
      options.system.showNotification('Vui lòng nhập số sê-ri thùng hợp lệ!', 'error');
      selectedSlotId.value = null;
      return;
    }
    
    const matchedSlot = jobOrderSlots.value.find(s => {
      const seqMatch = s.carton_sn.match(/\d{5}$/);
      return seqMatch ? parseInt(seqMatch[0]) === num : false;
    });
    
    if (!matchedSlot) {
      hasCartonNumberError.value = true;
      const prefix = options.currentProduct.value ? `${options.currentProduct.value.start_part || ''}${getActiveYYMM()}${options.currentProduct.value.middle_part || ''}` : '';
      const fullSn = `${prefix}${String(num).padStart(5, '0')}`;
      cartonNumberErrorText.value = `Sê-ri thùng ${fullSn} không nằm trong công lệnh!`;
      options.system.showNotification(`Sê-ri thùng ${fullSn} không nằm trong công lệnh!`, 'error');
      selectedSlotId.value = null;
      return;
    }
    
    if (matchedSlot.status === 'SCANNED') {
      hasCartonNumberError.value = true;
      cartonNumberErrorText.value = `Thùng sê-ri ${matchedSlot.carton_sn} đã đóng gói rồi!`;
      options.system.showNotification(`Thùng sê-ri ${matchedSlot.carton_sn} đã hoàn thành rồi!`, 'warning');
      selectedSlotId.value = null;
      return;
    }
    
    hasCartonNumberError.value = false;
    cartonNumberErrorText.value = '';
    selectSlot(matchedSlot);
  };

  watch(cartonNumberStr, (newVal) => {
    if (!newVal.trim()) {
      hasCartonNumberError.value = false;
      cartonNumberErrorText.value = '';
      return;
    }
    const num = parseInt(newVal);
    if (isNaN(num)) {
      hasCartonNumberError.value = true;
      cartonNumberErrorText.value = 'Số sê-ri không hợp lệ!';
      selectedSlotId.value = null;
      return;
    }
    
    if (jobOrderSlots.value.length > 0) {
      const matchedSlot = jobOrderSlots.value.find(s => {
        const seqMatch = s.carton_sn.match(/\d{5}$/);
        return seqMatch ? parseInt(seqMatch[0]) === num : false;
      });
      
      if (!matchedSlot) {
        hasCartonNumberError.value = true;
        const prefix = options.currentProduct.value ? `${options.currentProduct.value.start_part || ''}${getActiveYYMM()}${options.currentProduct.value.middle_part || ''}` : '';
        const fullSn = `${prefix}${String(num).padStart(5, '0')}`;
        cartonNumberErrorText.value = `Sê-ri thùng ${fullSn} không nằm trong công lệnh!`;
        selectedSlotId.value = null;
      } else if (matchedSlot.status === 'SCANNED') {
        hasCartonNumberError.value = true;
        cartonNumberErrorText.value = `Thùng sê-ri ${matchedSlot.carton_sn} đã đóng gói rồi!`;
        selectedSlotId.value = null;
      } else {
        hasCartonNumberError.value = false;
        cartonNumberErrorText.value = '';
        selectedSlotId.value = matchedSlot.id;
        const sn = matchedSlot.carton_sn;
        const seqMatch = sn.match(/\d{5}$/);
        if (seqMatch) options.customSN.value = parseInt(seqMatch[0]).toString();
        if (sn.length >= 6) options.customYYMM.value = sn.slice(2, 6);
        options.isSNManual.value = true;
      }
    } else {
      hasCartonNumberError.value = false;
      cartonNumberErrorText.value = '';
      selectedSlotId.value = null;
    }
  });

  return {
    jobOrderSlots,
    cartonNumberStr,
    selectedSlotId,
    hasCartonNumberError,
    cartonNumberErrorText,
    scannedCartonsCount,
    cartonNumberRange,
    selectSlot,
    handleCartonNumberSubmit,
    getActiveYYMM,
  };
}
