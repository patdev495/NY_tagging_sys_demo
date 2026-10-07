import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ref } from 'vue';
import { useErroSerialNumber } from '../composables/useErroSerialNumber';
import catalogApi from '../../../catalog/api';
import type { Product } from '../../../../types/api';

vi.mock('../../../catalog/api', () => ({
  default: {
    getNextSN: vi.fn(),
  },
}));

describe('useErroSerialNumber Composable (Strict Monotonic Sequence - ADR 0006)', () => {
  const mockProduct = ref<Product | null>({
    id: 10,
    customer_id: 2,
    item_name: 'Erro-01',
    packed_qty: 190,
    pkg_prefix: 'VHK0010237',
    template_type: 'erro_01',
    allow_partial: 0,
  });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('computes S/N preview with default fallback format and auto mode', () => {
    const { currentSNPreview, isAutoSN } = useErroSerialNumber(mockProduct);

    expect(isAutoSN.value).toBe(true);
    expect(currentSNPreview.value).toMatch(/^VHK0010237\d{4}000001$/);
  });

  it('updates sequence and YYMM when fetchNextSN succeeds', async () => {
    vi.mocked(catalogApi.getNextSN).mockResolvedValueOnce({
      data: { next_seq: 42, yymm: '2608' },
    } as any);

    const { fetchNextSN, currentSNPreview, autoSequence } = useErroSerialNumber(mockProduct);

    await fetchNextSN();

    expect(autoSequence.value).toBe(42);
    expect(currentSNPreview.value).toBe('VHK00102372608000042');
  });

  it('strictly advances sequence automatically on advanceSequence without manual mode', () => {
    const { autoSequence, advanceSequence, isAutoSN } = useErroSerialNumber(mockProduct);

    expect(isAutoSN.value).toBe(true);
    autoSequence.value = 10;
    advanceSequence();
    expect(autoSequence.value).toBe(11);
  });

  it('formats 17-char serial number for erro_03 products', () => {
    const tem3Product = ref<Product | null>({
      id: 30,
      customer_id: 2,
      item_name: '2M21-00508-0004H',
      packed_qty: 190,
      pkg_prefix: '1012665',
      template_type: 'erro_03',
      allow_partial: 0,
    });

    const { currentSNPreview, autoSequence } = useErroSerialNumber(tem3Product);
    autoSequence.value = 1;

    expect(currentSNPreview.value).toMatch(/^1012665\d{6}0001$/);
    expect(currentSNPreview.value.length).toBe(17);
  });

  it('uses the server-provided PD027032 Carton ID preview for erro_04 products', async () => {
    const erro04Product = ref<Product | null>({
      id: 40,
      customer_id: 2,
      item_name: 'G111A1A',
      packed_qty: 120,
      template_type: 'erro_04',
      carton_id_prefix: 'H',
      allow_partial: 0,
    });
    vi.mocked(catalogApi.getNextSN).mockResolvedValueOnce({
      data: { next_seq: 10, next_sn: 'H69C000A', carton_id_prefix: 'H' },
    } as any);

    const { fetchNextSN, currentSNPreview } = useErroSerialNumber(erro04Product);
    await fetchNextSN();

    expect(currentSNPreview.value).toBe('H69C000A');
  });

  it('uses server-provided Carton SN and calculates 18-char preview for erro_05 products', async () => {
    const erro05Product = ref<Product | null>({
      id: 50,
      customer_id: 2,
      item_name: '1414-0GDA0BV',
      packed_qty: 1000,
      template_type: 'erro_05',
      pkg_prefix: 'MC220TW1',
      allow_partial: 0,
    });

    const { fetchNextSN, currentSNPreview, autoSequence } = useErroSerialNumber(erro05Product);
    autoSequence.value = 50001;

    // Verify local preview (18 chars, format MC220TW12{YY}{WW}50001)
    expect(currentSNPreview.value).toMatch(/^MC220TW12\d{4}50001$/);
    expect(currentSNPreview.value.length).toBe(18);

    // Verify server-provided SN
    vi.mocked(catalogApi.getNextSN).mockResolvedValueOnce({
      data: { next_seq: 50002, next_sn: 'MC220TW12263750002', pkg_prefix: 'MC220TW1', date_code: '2637' },
    } as any);

    await fetchNextSN();
    expect(currentSNPreview.value).toBe('MC220TW12263750002');
  });
});
