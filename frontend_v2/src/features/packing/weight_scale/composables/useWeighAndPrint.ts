import { ref, computed, type Ref } from 'vue';
import i18n from '../../../../i18n';
import packingApi from '../../api';
import printApi from '../../../print/api';
import { evaluateScaleTolerance, type ScaleToleranceResult } from '../../utils/scaleTolerance';
import type { Product, Carton, ScaleReading, ScaleStatus } from '../../../../types/api';

export interface WeighAndPrintSettings {
  agentUrl?: string;
  printerName?: string;
  templatePath?: string;
  stationId?: string;
  localTemplateDir?: string;
}

export interface UseWeighAndPrintOptions {
  selectedProduct: Ref<Product | null>;
  activeJobOrder?: Ref<string>;
  activePO: Ref<string>;
  activeLot: Ref<string>;
  isAgentOnline: Ref<boolean>;
  scaleReading: Ref<ScaleReading>;
  scaleStatus: Ref<ScaleStatus>;
  advanceSequence: () => void;
  notify?: (message: string, type: 'info' | 'success' | 'warning' | 'error') => void;
  getSettings?: () => WeighAndPrintSettings;
  openProductModal?: () => void;
  openBatchModal?: () => void;
}

export function useWeighAndPrint(options: UseWeighAndPrintOptions) {
  const t = i18n.global.t;
  const {
    selectedProduct,
    activeJobOrder,
    activePO,
    activeLot,
    isAgentOnline,
    scaleReading,
    scaleStatus,
    advanceSequence,
    notify,
    getSettings = (): WeighAndPrintSettings => ({}),
    openProductModal,
    openBatchModal,
  } = options;

  const isPrinting = ref(false);
  const sessionPackedCount = ref<number>(
    Number(sessionStorage.getItem('erro_session_count') || '0')
  );
  const lastPackedCarton = ref<Carton | null>(null);

  const showToleranceErrorModal = ref(false);
  const toleranceErrorDetails = ref<{
    status: string;
    title: string;
    message: string;
    currentWeight: number;
    minWeight: number;
    maxWeight: number;
  } | null>(null);

  const toleranceResult = computed<ScaleToleranceResult>(() => {
    return evaluateScaleTolerance({
      isConnected: isAgentOnline.value && scaleStatus.value.connected,
      currentWeight: scaleReading.value.weight,
      isStable: scaleReading.value.is_stable,
      product: selectedProduct.value,
    });
  });

  const getToleranceTitle = (status: string) => {
    switch (status) {
      case 'UNDERWEIGHT': return t('erro.underweight_title');
      case 'OVERWEIGHT': return t('erro.overweight_title');
      case 'UNSTABLE': return t('erro.unstable_title');
      case 'NO_PRODUCT': return t('erro.no_product_title');
      case 'AGENT_OFFLINE': return t('erro.agent_offline_title');
      case 'DISCONNECTED': return t('erro.scale_disconnected_title');
      default: return t('erro.tolerance_title');
    }
  };

  const getToleranceMessage = (status: string) => {
    const key = ({ DISCONNECTED: 'disconnected_message', UNSTABLE: 'unstable_message', UNDERWEIGHT: 'underweight_message', OVERWEIGHT: 'overweight_message', READY: 'ready_message' } as Record<string, string>)[status];
    return t(`erro.${key || 'tolerance_title'}`);
  };

  const calculateGaugePercent = (weight: number, target: number) => {
    if (!target || target <= 0) return 0;
    const pct = (weight / target) * 100;
    return Math.min(Math.max(pct, 0), 100);
  };

  const triggerWeighAndPrint = async () => {
    if (!selectedProduct.value) {
      notify?.(t('erro.choose_product'), 'warning');
      openProductModal?.();
      return;
    }

    const isTem2 = selectedProduct.value.template_type === 'erro_02';
    const isTem3 = selectedProduct.value.template_type === 'erro_03';
    const isTem5 = selectedProduct.value.template_type === 'erro_05';
    if (!isTem2 && !isTem3 && !isTem5 && !activePO.value?.trim()) {
      notify?.(t('erro.po_required_placeholder'), 'warning');
      openBatchModal?.();
      return;
    }

    if (!toleranceResult.value.canPrint) {
      toleranceErrorDetails.value = {
        status: toleranceResult.value.status,
        title: getToleranceTitle(toleranceResult.value.status),
        message: getToleranceMessage(toleranceResult.value.status),
        currentWeight: scaleReading.value.weight,
        minWeight: selectedProduct.value?.min_weight ?? 0.150,
        maxWeight: selectedProduct.value?.max_weight ?? 0.200,
      };
      showToleranceErrorModal.value = true;
      return;
    }

    if (isPrinting.value) return;

    isPrinting.value = true;
    const currentWeight = scaleReading.value.weight;
    const settings = getSettings();

    try {
      // 1. Call Backend API to allocate the next Erro serial number and generate BTXML.
      const res = await packingApi.weighPackCarton({
        product_id: selectedProduct.value.id,
        weight: currentWeight,
        job_order: activeJobOrder?.value?.trim() || undefined,
        po_number: isTem2 ? undefined : (activePO.value?.trim() || undefined),
        lot_number: undefined,
        printer_name: settings.printerName || undefined,
        template_path: settings.templatePath || undefined,
        station_id: settings.stationId || undefined,
      });

      const newCarton = res.data;
      const btxmlContent = (newCarton as any).btxml;

      if (!btxmlContent) {
        throw new Error('Backend did not return BTXML payload');
      }

      // 2. Send BTXML to Print Agent
      const agentUrl = settings.agentUrl || 'http://127.0.0.1:8080';
      const printResult = await printApi.agentPrint(
        agentUrl,
        btxmlContent,
        settings.printerName || undefined,
        settings.localTemplateDir || undefined
      );

      // If PDF export, trigger automatic download / view
      if (printResult?.type === 'pdf' && printResult?.data) {
        const link = document.createElement('a');
        link.href = `data:application/pdf;base64,${printResult.data}`;
        link.download = `${newCarton.carton_sn || 'label'}.pdf`;
        link.click();
      }

      // 3. Confirm SUCCESS status on backend
      try {
        await printApi.updateCartonStatus(newCarton.id, 'SUCCESS');
        newCarton.status = 'SUCCESS';
      } catch (e) {
        console.warn('Status confirmation warning:', e);
      }

      // 4. Update session and last carton
      lastPackedCarton.value = newCarton;
      sessionPackedCount.value += 1;
      sessionStorage.setItem('erro_session_count', String(sessionPackedCount.value));

      // 5. Advance serial number counter
      advanceSequence();

      notify?.(t('erro.print_success', { sn: newCarton.carton_sn }), 'success');
    } catch (err: any) {
      console.error('Erro print failed:', err);
      notify?.(t('erro.print_failed'), 'error');
    } finally {
      isPrinting.value = false;
    }
  };

  const resetSessionCount = () => {
    if (confirm(t('erro.confirm_reset_counter'))) {
      sessionPackedCount.value = 0;
      sessionStorage.setItem('erro_session_count', '0');
    }
  };

  return {
    isPrinting,
    sessionPackedCount,
    lastPackedCarton,
    showToleranceErrorModal,
    toleranceErrorDetails,
    toleranceResult,
    calculateGaugePercent,
    triggerWeighAndPrint,
    resetSessionCount,
    getToleranceTitle,
  };
}
