import { ref, computed, nextTick, watch, type Ref } from 'vue';
import { useI18n } from 'vue-i18n';
import packingApi from '../api';
import jobOrderApi from '../../job_order/api';
import printApi from '../../print/api';
import { useJobOrderSlots } from './useJobOrderSlots';
import type { Product, Carton, JobOrderSlot, JobOrderDetails, ItemSNConflictResponse } from '../../../types/api';

export interface UseJobOrderWorkflowOptions {
  system: any;
  currentProduct: Ref<Product | null>;
  focusScan: () => void;
  checkTemplateExists: () => Promise<void>;
  startPolling: (intervalMs?: number) => void;
  stopPolling: () => void;
  playScanAlert: () => void;
  jobOrderInputRef?: Ref<{ focusInput: () => void } | null>;
  cartonVerificationModalRef?: Ref<{ focusInput: () => void } | null>;
}

export function useJobOrderWorkflow(options: UseJobOrderWorkflowOptions) {
  const { t } = useI18n();

  const IS_DEMO = import.meta.env.VITE_DEMO_MODE === 'true';
  const currentStep = ref<number>(1);
  const inputJobOrder = ref<string>(IS_DEMO ? '1001' : '');
  const isLoadingJobOrder = ref<boolean>(false);
  const jobOrderDetails = ref<JobOrderDetails | null>(null);
  const jobOrder = ref<string>('');
  const cartonOrigin = ref<string>('VN');
  const customSN = ref<string>('');
  const snPattern = ref<string>('AS');
  const customYYMM = ref<string>('');
  const awaitingNext = ref<boolean>(false);
  const suggestedSNValue = ref<number>(1);
  const suggestedSNPreview = ref<string>('');
  const backupScannedItems = ref<string[]>([]);
  const scannedItems = ref<string[]>([]);
  const scanBuffer = ref<string>('');
  const invalidScans = ref<{ sn: string; time: string; reason: string; type: 'pattern' | 'duplicate' | 'lockdown' }[]>([]);
  const overflowScans = ref<{ sn: string; time: string; reason: string }[]>([]);
  const lastCarton = ref<(Carton & { status?: string, items?: { item_sn: string }[] }) | null>(null);
  const hadJobOrder = ref<boolean>(false);
  const savedSessionState = ref<any>(null);
  const isRescanMode = ref<boolean>(false);
  const rescanCartonSN = ref<string>('');
  const rescanCartonId = ref<number | null>(null);
  const isCheckingItemSN = ref<boolean>(false);
  const showItemSNConflictModal = ref<boolean>(false);
  const itemSNConflict = ref<ItemSNConflictResponse | null>(null);
  const isSNManual = ref<boolean>(false);
  const snExists = ref<boolean>(false);
  const showSettings = ref<boolean>(false);
  const showEmergencyModal = ref<boolean>(false);
  const showCartonSlotsModal = ref<boolean>(false);
  const showVerificationModal = ref<boolean>(false);
  const cartonToVerify = ref<(Carton & { status?: string, items?: { item_sn: string }[] }) | null>(null);
  const hasJobOrderError = ref<boolean>(false);
  const jobOrderErrorText = ref<string>('');

  let snCheckTimer: ReturnType<typeof setTimeout> | null = null;
  let onFinalizeCartonCallback: (() => Promise<void>) | null = null;

  const setOnFinalizeCarton = (cb: () => Promise<void>) => { onFinalizeCartonCallback = cb; };

  const slotsManager = useJobOrderSlots({
    system: options.system,
    currentProduct: options.currentProduct,
    customYYMM,
    customSN,
    suggestedSNPreview,
    isSNManual,
    scannedItems,
    focusScan: options.focusScan,
    confirmDiscardMsg: t('packing.switch_slot_confirm'),
  });

  const {
    jobOrderSlots, cartonNumberStr, selectedSlotId, hasCartonNumberError,
    cartonNumberErrorText, scannedCartonsCount, cartonNumberRange,
    selectSlot, handleCartonNumberSubmit, getActiveYYMM
  } = slotsManager;

  const progressPercent = computed(() => options.currentProduct.value ? Math.round((scannedItems.value.length / options.currentProduct.value.packed_qty) * 100) : 0);

  const snPreview = computed(() => {
    if (!options.currentProduct.value) return '';
    if (!isSNManual.value && suggestedSNPreview.value) return suggestedSNPreview.value;
    const seq = customSN.value || suggestedSNValue.value || '1';
    const prefix = `${options.currentProduct.value.start_part || ''}${getActiveYYMM()}${options.currentProduct.value.middle_part || ''}`;
    return `${prefix}${String(seq).padStart(5, '0')}`;
  });

  const submitJobOrder = async () => {
    const jo = inputJobOrder.value.trim();
    if (!jo) return;
    isLoadingJobOrder.value = true;
    hasJobOrderError.value = false;
    jobOrderErrorText.value = '';
    // A new Job Order must never inherit partially scanned items from a prior browser session.
    scannedItems.value = [];
    backupScannedItems.value = [];
    lastCarton.value = null;
    cartonToVerify.value = null;
    showVerificationModal.value = false;
    selectedSlotId.value = null;
    try {
      const res = await jobOrderApi.getJobOrderDetails(jo);
      jobOrderDetails.value = res.data;
      jobOrder.value = res.data.job_order;
      jobOrderSlots.value = res.data.slots;
      options.currentProduct.value = res.data.product;
      // A saved browser session may contain a prior operator's custom pattern.
      // Every newly loaded UI Job Order must begin with the standard AS prefix.
      snPattern.value = 'AS';
      currentStep.value = 2;
      options.system.showNotification('Đã tải thông tin công lệnh thành công!', 'success');
      
      if (res.data.product) {
        try {
          const lastCartonRes = await packingApi.getLastCarton(res.data.product.id, res.data.job_order);
          if (lastCartonRes.data) {
            lastCarton.value = lastCartonRes.data;
            if (lastCartonRes.data.status === 'FAILED' && lastCartonRes.data.items) {
              backupScannedItems.value = lastCartonRes.data.items.map((i: any) => i.item_sn);
            }
            if (lastCartonRes.data.status === 'PRINTED') {
              showVerificationModal.value = true;
              cartonToVerify.value = lastCartonRes.data;
              if (lastCartonRes.data.items) scannedItems.value = lastCartonRes.data.items.map((i: any) => i.item_sn);
            }
          }
        } catch (err) { console.warn('Error fetching last carton:', err); }
      }
    } catch (err: any) {
      const detail = t('packing.job_order_not_found', { jo });
      hasJobOrderError.value = true;
      jobOrderErrorText.value = detail;
      options.system.showNotification(detail, 'error');
    } finally { isLoadingJobOrder.value = false; }
  };

  const changeJobOrder = () => {
    if (scannedItems.value.length > 0 && !confirm(t('packing.change_job_order_confirm'))) return;
    currentStep.value = 1;
    inputJobOrder.value = '';
    jobOrder.value = '';
    jobOrderDetails.value = null;
    jobOrderSlots.value = [];
    selectedSlotId.value = null;
    cartonNumberStr.value = '';
    options.currentProduct.value = null;
    scannedItems.value = [];
    lastCarton.value = null;
    customSN.value = '';
    suggestedSNPreview.value = '';
    customYYMM.value = '';
    snPattern.value = 'AS';
    isSNManual.value = false;
    showCartonSlotsModal.value = false;
    nextTick(() => { if (options.jobOrderInputRef?.value) options.jobOrderInputRef.value.focusInput(); });
  };

  const refreshJobOrderDetails = async () => {
    if (!jobOrder.value) return;
    try {
      const res = await jobOrderApi.getJobOrderDetails(jobOrder.value);
      if (res.data) {
        jobOrderDetails.value = res.data;
        if (res.data.product) options.currentProduct.value = res.data.product;
        if (res.data.slots) jobOrderSlots.value = res.data.slots;
      }
    } catch (err) { console.warn('Failed to refresh job order details:', err); }
  };

  const enterScanning = async () => {
    currentStep.value = 3;
    await refreshJobOrderDetails();
    // A resumed Carton may already be verified. Keep its scanned items visible
    // until the operator explicitly starts the next Carton; do not switch slots.
    if (awaitingNext.value) {
      options.checkTemplateExists();
      options.focusScan();
      return;
    }
    const firstPending = jobOrderSlots.value.find(s => s.status === 'PENDING');
    if (firstPending) selectSlot(firstPending);
    else if (jobOrderSlots.value.length > 0) selectSlot(jobOrderSlots.value[0]);
    options.checkTemplateExists();
    options.focusScan();
  };

  const handleSlotClickInModal = (slot: JobOrderSlot) => {
    selectSlot(slot);
    if (selectedSlotId.value === slot.id) showCartonSlotsModal.value = false;
  };

  const refreshNextSN = async () => {
    if (currentStep.value === 3 || !options.currentProduct.value) return;
    try {
      const snRes = await packingApi.getNextSN(options.currentProduct.value.id, customYYMM.value);
      const data = snRes.data as any;
      const newSeq = data.next_seq || (data.next_sn ? parseInt(data.next_sn.match(/\d{5}$/)?.[0] || '0') : 1);
      if (newSeq) {
        suggestedSNValue.value = newSeq;
        suggestedSNPreview.value = data.next_sn || '';
        if (!isSNManual.value) customSN.value = newSeq.toString();
      }
    } catch (err) { console.warn('Sync SN failed:', err); }
  };

  const processSingleScan = async (sn: string) => {
    if (!sn || !options.currentProduct.value) return;

    if (awaitingNext.value) {
      options.playScanAlert();
      invalidScans.value.push({
        sn,
        time: new Date().toLocaleTimeString(),
        reason: 'Thùng đã đóng — Bấm "Thùng tiếp theo" hoặc phím Space',
        type: 'lockdown'
      });
      options.system.showNotification(t('packing.carton_full', { sn }), 'warning');
      return;
    }

    if (!jobOrder.value) { options.system.showNotification(t('packing.enter_job_order'), 'error'); return; }

    const hasRealInvalid = invalidScans.value.some(s => ['pattern', 'duplicate', 'lockdown'].includes(s.type));
    if (hasRealInvalid) { 
      options.playScanAlert(); 
      invalidScans.value.push({ sn, time: new Date().toLocaleTimeString(), reason: 'Station locked — clear errors first', type: 'lockdown' }); 
      options.system.showNotification(t('packing.station_locked'), 'error'); 
      return; 
    }

    if (snPattern.value && !sn.startsWith(snPattern.value)) { 
      options.playScanAlert(); 
      invalidScans.value.push({ sn, time: new Date().toLocaleTimeString(), reason: 'Prefix mismatch', type: 'pattern' }); 
      options.system.showNotification(t('packing.prefix_mismatch', { sn }), 'error'); 
      return; 
    }
    
    if (scannedItems.value.includes(sn)) { 
      options.playScanAlert(); 
      invalidScans.value.push({ sn, time: new Date().toLocaleTimeString(), reason: 'Duplicate S/N', type: 'duplicate' }); 
      options.system.showNotification(t('packing.duplicate_sn'), 'warning'); 
      return; 
    }

    if (scannedItems.value.length >= options.currentProduct.value.packed_qty) {
      options.playScanAlert();
      overflowScans.value.push({ sn, time: new Date().toLocaleTimeString(), reason: 'Carton Full' });
      options.system.showNotification(t('packing.carton_full'), 'error');
      return;
    }

    isCheckingItemSN.value = true;
    try {
      const response = await packingApi.getItemSNConflicts(sn, rescanCartonId.value ?? undefined);
      if (response.data.conflicts.length > 0) {
        options.playScanAlert();
        itemSNConflict.value = response.data;
        showItemSNConflictModal.value = true;
        options.system.showNotification(t('packing.item_sn_conflict'), 'warning');
        return;
      }
    } catch {
      options.playScanAlert();
      invalidScans.value.push({ sn, time: new Date().toLocaleTimeString(), reason: 'Không thể kiểm tra mã trùng', type: 'lockdown' });
      options.system.showNotification(t('packing.item_sn_check_unavailable'), 'error');
      return;
    } finally {
      isCheckingItemSN.value = false;
    }

    scannedItems.value.push(sn);
    if (scannedItems.value.length === options.currentProduct.value.packed_qty && onFinalizeCartonCallback) {
      onFinalizeCartonCallback(); 
    }
  };

  const handleScan = async () => {
    const rawInput = scanBuffer.value.trim();
    if (!rawInput) return;
    const sns = rawInput.split(/\s*[\n\r\t,]+\s*/).map(s => s.trim()).filter(s => s.length > 0);
    if (sns.length === 0) return;
    for (const sn of sns) {
      await processSingleScan(sn);
      if (showItemSNConflictModal.value || isCheckingItemSN.value) break;
    }
    scanBuffer.value = '';
  };

  const handleRescan = (carton: Carton) => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
    if (hadJobOrder.value) {
      savedSessionState.value = {
        currentStep: currentStep.value, selectedSlotId: selectedSlotId.value,
        cartonNumberStr: cartonNumberStr.value, customSN: customSN.value,
        customYYMM: customYYMM.value, isSNManual: isSNManual.value,
        scannedItems: [...scannedItems.value], cartonOrigin: cartonOrigin.value,
        jobOrder: jobOrder.value, currentProduct: options.currentProduct.value
      };
    }

    options.currentProduct.value = carton.product || null;
    scannedItems.value = [];
    invalidScans.value = [];
    overflowScans.value = [];
    awaitingNext.value = false;
    lastCarton.value = carton;
    customSN.value = '';
    suggestedSNPreview.value = '';
    snPattern.value = 'AS';
    jobOrder.value = carton.job_order || 'EMERGENCY_RESCAN';
    cartonOrigin.value = carton.carton_origin || 'VN';
    isRescanMode.value = true;
    rescanCartonSN.value = carton.carton_sn;
    rescanCartonId.value = carton.id;
    showEmergencyModal.value = false;
    currentStep.value = 3;
    options.system.showNotification(`RESCAN MODE ACTIVE for ${carton.carton_sn}`, 'warning');
    options.startPolling(5000);
    options.focusScan();
  };

  const cancelRescan = () => {
    isRescanMode.value = false;
    rescanCartonSN.value = '';
    rescanCartonId.value = null;
    options.stopPolling();
    if (!hadJobOrder.value) resetSession();
    else {
      if (savedSessionState.value) {
        const s = savedSessionState.value;
        currentStep.value = s.currentStep;
        selectedSlotId.value = s.selectedSlotId;
        cartonNumberStr.value = s.cartonNumberStr;
        customSN.value = s.customSN;
        customYYMM.value = s.customYYMM;
        isSNManual.value = s.isSNManual;
        scannedItems.value = s.scannedItems;
        cartonOrigin.value = s.cartonOrigin;
        jobOrder.value = s.jobOrder;
        options.currentProduct.value = s.currentProduct;
        savedSessionState.value = null;
      }
      options.focusScan();
    }
  };

  const startNextCarton = () => { 
    const hasErrors = invalidScans.value.length > 0 || overflowScans.value.length > 0;
    if (hasErrors) {
      options.playScanAlert();
      options.system.showNotification('Vui lòng xóa các lỗi quét trước khi chuyển sang thùng tiếp theo!', 'error');
      return;
    }

    awaitingNext.value = false; 
    scannedItems.value = []; 
    invalidScans.value = []; 
    overflowScans.value = [];
    customSN.value = '';
    suggestedSNPreview.value = '';
    isRescanMode.value = false;
    rescanCartonSN.value = '';
    rescanCartonId.value = null;

    const nextPending = jobOrderSlots.value.find(s => s.status === 'PENDING');
    if (nextPending) {
      selectSlot(nextPending, false);
    } else {
      selectedSlotId.value = null;
      cartonNumberStr.value = '';
    }
    options.focusScan(); 
  };

  const resetSession = () => { 
    if (scannedItems.value.length > 0 && !confirm(t('packing.reset_session_confirm'))) return;
    currentStep.value = 1;
    inputJobOrder.value = '';
    jobOrder.value = '';
    jobOrderDetails.value = null;
    jobOrderSlots.value = [];
    selectedSlotId.value = null;
    cartonNumberStr.value = '';
    options.currentProduct.value = null; 
    scannedItems.value = []; 
    invalidScans.value = []; 
    overflowScans.value = []; 
    awaitingNext.value = false; 
    isRescanMode.value = false;
    rescanCartonSN.value = '';
    rescanCartonId.value = null;
    snPattern.value = 'AS';
    scanBuffer.value = ''; 
    showVerificationModal.value = false;
    cartonToVerify.value = null;
    showCartonSlotsModal.value = false;
    nextTick(() => { if (options.jobOrderInputRef?.value) options.jobOrderInputRef.value.focusInput(); }); 
  };

  watch(inputJobOrder, () => {
    hasJobOrderError.value = false;
    jobOrderErrorText.value = '';
  });

  watch(customSN, (val) => {
    if (val && val !== suggestedSNValue.value.toString()) isSNManual.value = true;
  });

  watch(snPreview, (newVal) => {
    if (!newVal || !isSNManual.value || isRescanMode.value) {
      snExists.value = false;
      return;
    }
    if (snCheckTimer) clearTimeout(snCheckTimer);
    snCheckTimer = setTimeout(async () => {
      try {
        const res = await printApi.searchCarton(newVal);
        snExists.value = !!res.data;
      } catch {
        snExists.value = false;
      }
    }, 500);
  });

  return {
    currentStep, inputJobOrder, isLoadingJobOrder, jobOrderDetails, jobOrderSlots,
    cartonNumberStr, selectedSlotId, jobOrder, cartonOrigin, customSN, snPattern,
    customYYMM, awaitingNext, suggestedSNValue, suggestedSNPreview, backupScannedItems,
    scannedItems, scanBuffer, invalidScans, overflowScans, lastCarton, hadJobOrder,
    savedSessionState, isRescanMode, rescanCartonSN, rescanCartonId, isCheckingItemSN,
    showItemSNConflictModal, itemSNConflict, isSNManual, snExists, showSettings,
    showEmergencyModal, showCartonSlotsModal, showVerificationModal, cartonToVerify,
    hasCartonNumberError, cartonNumberErrorText, hasJobOrderError, jobOrderErrorText,
    scannedCartonsCount, progressPercent, snPreview, cartonNumberRange, submitJobOrder,
    changeJobOrder, refreshJobOrderDetails, enterScanning, selectSlot, handleSlotClickInModal,
    handleCartonNumberSubmit, refreshNextSN, processSingleScan, handleScan, handleRescan,
    cancelRescan, startNextCarton, resetSession, setOnFinalizeCarton,
  };
}
