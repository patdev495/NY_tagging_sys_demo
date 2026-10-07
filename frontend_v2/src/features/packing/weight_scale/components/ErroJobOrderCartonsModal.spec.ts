import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import ErroJobOrderCartonsModal from './ErroJobOrderCartonsModal.vue';
import historyApi from '../../../history/api';

vi.mock('../../../history/api', () => ({
  default: {
    getCartons: vi.fn(),
  },
}));

describe('ErroJobOrderCartonsModal', () => {
  const sampleProduct = {
    id: 91,
    item_name: '840-00092',
    packed_qty: 190,
    target_weight: 6.5,
    min_weight: 5.5,
    max_weight: 5.9,
    weight_unit: 'kg',
  } as any;

  const sampleCartons = [
    {
      id: 1,
      carton_sn: 'ERRO-SN-001',
      job_order: '1259487',
      weight: 5.72,
      po_number: 'PO-TEST-1',
      lot_number: 'LOT-999',
      status: 'SUCCESS',
      created_at: '2026-09-16T08:30:00.000Z',
    },
    {
      id: 2,
      carton_sn: 'ERRO-SN-002',
      job_order: '1259487',
      weight: 5.75,
      po_number: 'PO-TEST-2',
      lot_number: 'LOT-888',
      status: 'SUCCESS',
      created_at: '2026-09-16T08:35:00.000Z',
    },
  ];

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches and renders cartons for the given job order', async () => {
    vi.mocked(historyApi.getCartons).mockResolvedValue({
      data: {
        total: 2,
        items: sampleCartons as any,
      },
    } as any);

    const wrapper = mount(ErroJobOrderCartonsModal, {
      props: {
        show: true,
        jobOrder: '1259487',
        product: sampleProduct,
        plannedCartons: 120,
        totalQty: 22800,
      },
    });

    await flushPromises();

    expect(historyApi.getCartons).toHaveBeenCalledWith({
      job_order: '1259487',
      limit: 200,
    });

    expect(wrapper.text()).toContain('ERRO-SN-001');
    expect(wrapper.text()).toContain('ERRO-SN-002');
    expect(wrapper.text()).toContain('5.72 kg');
    expect(wrapper.text()).toContain('PO-TEST-1');
    expect(wrapper.text()).toContain('LOT-999');
    expect(wrapper.text()).toContain('2 / 120 Thùng');
  });

  it('displays empty state when no cartons exist', async () => {
    vi.mocked(historyApi.getCartons).mockResolvedValue({
      data: {
        total: 0,
        items: [],
      },
    } as any);

    const wrapper = mount(ErroJobOrderCartonsModal, {
      props: {
        show: true,
        jobOrder: '1259487',
        product: sampleProduct,
        plannedCartons: 120,
        totalQty: 22800,
      },
    });

    await flushPromises();

    expect(wrapper.text()).toContain('Chưa có thùng nào được đóng cho công lệnh này');
  });

  it('filters cartons by search keyword', async () => {
    vi.mocked(historyApi.getCartons).mockResolvedValue({
      data: {
        total: 2,
        items: sampleCartons as any,
      },
    } as any);

    const wrapper = mount(ErroJobOrderCartonsModal, {
      props: {
        show: true,
        jobOrder: '1259487',
        product: sampleProduct,
        plannedCartons: 120,
        totalQty: 22800,
      },
    });

    await flushPromises();

    const searchInput = wrapper.find('input[placeholder*="Tìm kiếm"]');
    await searchInput.setValue('002');

    expect(wrapper.text()).not.toContain('ERRO-SN-001');
    expect(wrapper.text()).toContain('ERRO-SN-002');
  });

  it('emits close when clicking close button', async () => {
    vi.mocked(historyApi.getCartons).mockResolvedValue({
      data: { total: 0, items: [] },
    } as any);

    const wrapper = mount(ErroJobOrderCartonsModal, {
      props: {
        show: true,
        jobOrder: '1259487',
        product: sampleProduct,
        plannedCartons: 120,
        totalQty: 22800,
      },
    });

    const closeBtn = wrapper.find('button[title*="Đóng"]');
    await closeBtn.trigger('click');

    expect(wrapper.emitted('close')).toBeTruthy();
  });
});
