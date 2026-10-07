import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ref } from 'vue';
import { useWeighAndPrint } from '../composables/useWeighAndPrint';
import packingApi from '../../api';
import printApi from '../../../print/api';
import type { Product, ScaleReading, ScaleStatus } from '../../../../types/api';

vi.mock('../../api', () => ({
  default: {
    weighPackCarton: vi.fn(),
  },
}));

vi.mock('../../../print/api', () => ({
  default: {
    agentPrint: vi.fn(),
    updateCartonStatus: vi.fn(),
  },
}));

describe('useWeighAndPrint Composable (Strict Monotonic - ADR 0006)', () => {
  const selectedProduct = ref<Product | null>({
    id: 10,
    customer_id: 2,
    item_name: 'Erro-01',
    packed_qty: 190,
    pkg_prefix: 'VHK0010237',
    template_type: 'erro_01',
    allow_partial: 0,
    min_weight: 12.3,
    target_weight: 12.5,
    max_weight: 12.7,
  });

  const activePO = ref('PO-2026-001');
  const activeLot = ref('LOT-9988');
  const isAgentOnline = ref(true);
  const scaleReading = ref<ScaleReading>({
    weight: 12.502,
    unit: 'kg',
    is_stable: true,
    is_tare: false,
    is_net: false,
  });
  const scaleStatus = ref<ScaleStatus>({
    connected: true,
    port: 'COM3',
    baudrate: 9600,
    is_streaming: true,
  });
  const advanceSequence = vi.fn();
  const notify = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('evaluates tolerance correctly as READY when weight is within tolerance and stable', () => {
    const { toleranceResult } = useWeighAndPrint({
      selectedProduct,
      activePO,
      activeLot,
      isAgentOnline,
      scaleReading,
      scaleStatus,
      advanceSequence,
      notify,
      getSettings: () => ({ agentUrl: 'http://127.0.0.1:8080' }),
    });

    expect(toleranceResult.value.status).toBe('READY');
    expect(toleranceResult.value.canPrint).toBe(true);
  });

  it('blocks printing and opens error modal when tolerance fails (e.g. underweight)', async () => {
    scaleReading.value.weight = 10.0; // underweight

    const { toleranceResult, triggerWeighAndPrint, showToleranceErrorModal, toleranceErrorDetails } = useWeighAndPrint({
      selectedProduct,
      activePO,
      activeLot,
      isAgentOnline,
      scaleReading,
      scaleStatus,
      advanceSequence,
      notify,
      getSettings: () => ({ agentUrl: 'http://127.0.0.1:8080' }),
    });

    expect(toleranceResult.value.canPrint).toBe(false);

    await triggerWeighAndPrint();

    expect(showToleranceErrorModal.value).toBe(true);
    expect(toleranceErrorDetails.value?.status).toBe('UNDERWEIGHT');
    expect(packingApi.weighPackCarton).not.toHaveBeenCalled();
  });

  it('executes full weigh & print flow with strictly automatic sequence', async () => {
    scaleReading.value.weight = 12.505;

    vi.mocked(packingApi.weighPackCarton).mockResolvedValueOnce({
      data: {
        id: 123,
        carton_sn: 'VHK00102372608000001',
        weight: 12.505,
        status: 'PENDING',
        btxml: '<XMLScript Version="2.0"></XMLScript>',
      },
    } as any);

    vi.mocked(printApi.agentPrint).mockResolvedValueOnce({
      type: 'raw',
      status: 'success',
    } as any);

    vi.mocked(printApi.updateCartonStatus).mockResolvedValueOnce({} as any);

    const { triggerWeighAndPrint, lastPackedCarton, sessionPackedCount } = useWeighAndPrint({
      selectedProduct,
      activePO,
      activeLot,
      isAgentOnline,
      scaleReading,
      scaleStatus,
      advanceSequence,
      notify,
      getSettings: () => ({ agentUrl: 'http://127.0.0.1:8080' }),
    });

    sessionPackedCount.value = 0;
    await triggerWeighAndPrint();

    expect(packingApi.weighPackCarton).toHaveBeenCalledWith({
      product_id: 10,
      weight: 12.505,
      job_order: undefined,
      po_number: 'PO-2026-001',
      lot_number: undefined,
      printer_name: undefined,
      template_path: undefined,
      station_id: undefined,
    });
    expect(printApi.agentPrint).toHaveBeenCalled();
    expect(printApi.updateCartonStatus).toHaveBeenCalledWith(123, 'SUCCESS');
    expect(advanceSequence).toHaveBeenCalled();
    expect(lastPackedCarton.value?.carton_sn).toBe('VHK00102372608000001');
    expect(sessionPackedCount.value).toBe(1);
    expect(notify).toHaveBeenCalledWith(expect.stringContaining('Đã in thành công'), 'success');
  });

  it('sends undefined po_number and lot_number for erro_02 products even if activePO has value', async () => {
    selectedProduct.value = {
      id: 20,
      item_name: 'G012C1B',
      template_type: 'erro_02',
      target_weight: 8.0,
      min_weight: 7.5,
      max_weight: 8.5,
      packed_qty: 25,
      weight_unit: 'kg',
    } as any;
    scaleReading.value = { weight: 8.05, unit: 'kg', is_stable: true };

    vi.mocked(packingApi.weighPackCarton).mockResolvedValueOnce({
      data: {
        id: 456,
        carton_sn: '(00) 0 37033907 0000001 5',
        btxml: '<XML>TEM2</XML>',
      },
    } as any);
    vi.mocked(printApi.agentPrint).mockResolvedValueOnce({ success: true } as any);
    vi.mocked(printApi.updateCartonStatus).mockResolvedValueOnce({} as any);

    const { triggerWeighAndPrint } = useWeighAndPrint({
      selectedProduct,
      activePO,
      activeLot,
      isAgentOnline,
      scaleReading,
      scaleStatus,
      advanceSequence,
      notify,
      getSettings: () => ({ agentUrl: 'http://127.0.0.1:8080' }),
    });

    await triggerWeighAndPrint();

    expect(packingApi.weighPackCarton).toHaveBeenCalledWith({
      product_id: 20,
      weight: 8.05,
      po_number: undefined,
      lot_number: undefined,
      printer_name: undefined,
      template_path: undefined,
      station_id: undefined,
    });
  });

  it('allows empty po_number for erro_03 products and calls packing API', async () => {
    selectedProduct.value = {
      id: 30,
      item_name: '2M21-00508-0004H',
      template_type: 'erro_03',
      target_weight: 6.0,
      min_weight: 5.0,
      max_weight: 7.0,
      packed_qty: 190,
      weight_unit: 'kg',
    } as any;
    activePO.value = '';
    activeLot.value = '92607933';
    scaleReading.value = { weight: 6.05, unit: 'kg', is_stable: true };

    vi.mocked(packingApi.weighPackCarton).mockResolvedValueOnce({
      data: {
        id: 789,
        carton_sn: '10126652609110001',
        btxml: '<XML>TEM3</XML>',
      },
    } as any);
    vi.mocked(printApi.agentPrint).mockResolvedValueOnce({ success: true } as any);
    vi.mocked(printApi.updateCartonStatus).mockResolvedValueOnce({} as any);

    const { triggerWeighAndPrint } = useWeighAndPrint({
      selectedProduct,
      activePO,
      activeLot,
      isAgentOnline,
      scaleReading,
      scaleStatus,
      advanceSequence,
      notify,
      getSettings: () => ({ agentUrl: 'http://127.0.0.1:8080' }),
    });

    await triggerWeighAndPrint();

    expect(packingApi.weighPackCarton).toHaveBeenCalledWith({
      product_id: 30,
      weight: 6.05,
      job_order: undefined,
      po_number: undefined,
      lot_number: undefined,
      printer_name: undefined,
      template_path: undefined,
      station_id: undefined,
    });
    expect(printApi.agentPrint).toHaveBeenCalled();
  });

  it('blocks erro_04 weigh and print if PO is missing and opens batch modal', async () => {
    selectedProduct.value = {
      id: 40,
      item_name: 'G111A1A',
      template_type: 'erro_04',
      target_weight: 5.0,
      min_weight: 0.0,
      max_weight: 10.0,
      packed_qty: 120,
      weight_unit: 'kg',
      carton_id_prefix: 'H',
      factory_item_code: '115-00020',
      revision: 'B',
    } as any;
    activePO.value = '';
    activeLot.value = 'LOT-04';
    scaleReading.value = { weight: 5.0, unit: 'kg', is_stable: true };

    const openBatchModal = vi.fn();
    const { triggerWeighAndPrint } = useWeighAndPrint({
      selectedProduct,
      activePO,
      activeLot,
      isAgentOnline,
      scaleReading,
      scaleStatus,
      advanceSequence,
      notify,
      openBatchModal,
      getSettings: () => ({ agentUrl: 'http://127.0.0.1:8080' }),
    });

    await triggerWeighAndPrint();

    expect(notify).toHaveBeenCalledWith('Ví dụ: B432-22156381 (bắt buộc)', 'warning');
    expect(openBatchModal).toHaveBeenCalled();
    expect(packingApi.weighPackCarton).not.toHaveBeenCalled();
  });

  it('executes erro_04 weigh and print with required PO while backend generates LOT', async () => {
    selectedProduct.value = {
      id: 40,
      item_name: 'G111A1A',
      template_type: 'erro_04',
      target_weight: 5.0,
      min_weight: 0.0,
      max_weight: 10.0,
      packed_qty: 120,
      weight_unit: 'kg',
      carton_id_prefix: 'H',
      factory_item_code: '115-00020',
      revision: 'B',
    } as any;
    activePO.value = 'PO-ERRO-1';
    activeLot.value = 'LOT-ERRO-1';
    scaleReading.value = { weight: 5.01, unit: 'kg', is_stable: true };

    vi.mocked(packingApi.weighPackCarton).mockResolvedValueOnce({
      data: {
        id: 101,
        carton_sn: 'H69C0001',
        po_number: 'PO-ERRO-1',
        lot_number: 'LOT-ERRO-1',
        btxml: '<XML>ERRO-04</XML>',
      },
    } as any);
    vi.mocked(printApi.agentPrint).mockResolvedValueOnce({ success: true } as any);
    vi.mocked(printApi.updateCartonStatus).mockResolvedValueOnce({} as any);

    const { triggerWeighAndPrint, lastPackedCarton } = useWeighAndPrint({
      selectedProduct,
      activePO,
      activeLot,
      isAgentOnline,
      scaleReading,
      scaleStatus,
      advanceSequence,
      notify,
      getSettings: () => ({ agentUrl: 'http://127.0.0.1:8080' }),
    });

    await triggerWeighAndPrint();

    expect(packingApi.weighPackCarton).toHaveBeenCalledWith({
      product_id: 40,
      weight: 5.01,
      job_order: undefined,
      po_number: 'PO-ERRO-1',
      lot_number: undefined,
      printer_name: undefined,
      template_path: undefined,
      station_id: undefined,
    });
    expect(lastPackedCarton.value?.carton_sn).toBe('H69C0001');

    // Operator mutates the PO value; the backend continues to generate LOT.
    activePO.value = 'PO-ERRO-2';
    activeLot.value = 'LOT-ERRO-2';
    vi.mocked(packingApi.weighPackCarton).mockResolvedValueOnce({
      data: {
        id: 102,
        carton_sn: 'H69C0002',
        po_number: 'PO-ERRO-2',
        lot_number: 'LOT-ERRO-2',
        btxml: '<XML>ERRO-04-2</XML>',
      },
    } as any);

    await triggerWeighAndPrint();

    expect(packingApi.weighPackCarton).toHaveBeenLastCalledWith({
      product_id: 40,
      weight: 5.01,
      job_order: undefined,
      po_number: 'PO-ERRO-2',
      lot_number: undefined,
      printer_name: undefined,
      template_path: undefined,
      station_id: undefined,
    });
    expect(lastPackedCarton.value?.carton_sn).toBe('H69C0002');
  });

  it('allows erro_05 weigh and print with empty PO and empty Lot (optional / auto LotCode)', async () => {
    selectedProduct.value = {
      id: 50,
      item_name: '1414-0GDA0BV',
      template_type: 'erro_05',
      target_weight: 5.0,
      min_weight: 0.0,
      max_weight: 10.0,
      packed_qty: 1000,
      weight_unit: 'kg',
      pkg_prefix: 'MC220TW1',
      factory_item_code: '1HWU3023C1XX02NN9',
    } as any;
    activePO.value = '';
    activeLot.value = '';
    scaleReading.value = { weight: 5.0, unit: 'kg', is_stable: true };

    vi.mocked(packingApi.weighPackCarton).mockResolvedValueOnce({
      data: {
        id: 201,
        carton_sn: 'MC220TW12263750001',
        po_number: null,
        lot_number: '20260912',
        date_code: '2637',
        btxml: '<XML>ERRO-05</XML>',
      },
    } as any);

    const { triggerWeighAndPrint, lastPackedCarton } = useWeighAndPrint({
      selectedProduct,
      activePO,
      activeLot,
      isAgentOnline,
      scaleReading,
      scaleStatus,
      advanceSequence,
      notify,
      getSettings: () => ({ agentUrl: 'http://127.0.0.1:8080' }),
    });

    await triggerWeighAndPrint();

    expect(packingApi.weighPackCarton).toHaveBeenCalledWith({
      product_id: 50,
      weight: 5.0,
      po_number: undefined,
      lot_number: undefined,
      printer_name: undefined,
      template_path: undefined,
      station_id: undefined,
    });
    expect(printApi.agentPrint).toHaveBeenCalled();
    expect(lastPackedCarton.value?.carton_sn).toBe('MC220TW12263750001');
  });
});
