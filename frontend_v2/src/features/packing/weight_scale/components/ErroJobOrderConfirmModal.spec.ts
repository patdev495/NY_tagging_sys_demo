import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import ErroJobOrderConfirmModal from './ErroJobOrderConfirmModal.vue';
import type { ErroJobOrderResolution } from '../../../../types/api';

describe('ErroJobOrderConfirmModal', () => {
  const sampleResolution: ErroJobOrderResolution = {
    job_order: '1259487',
    factory_part_number: '1LAE0091C2U005MAAS',
    customer_ref: '840-00092',
    total_qty: 22800,
    planned_cartons: 120,
    packed_cartons_count: 0,
    name_mismatch: false,
    product: {
      id: 1,
      customer_id: 1,
      customer_name: 'Erro',
      item_name: '840-00092',
      customer_part_number: '840-00092',
      template_type: 'erro_01',
      packed_qty: 190,
      net_weight: 10.0,
      tolerance_percentage: 5.0,
    } as any,
  };

  it('renders job order details correctly', () => {
    const wrapper = mount(ErroJobOrderConfirmModal, {
      props: {
        show: true,
        resolution: sampleResolution,
        initialPo: '',
        initialLot: '',
      },
    });

    expect(wrapper.text()).toContain('1259487');
    expect(wrapper.text()).toContain('1LAE0091C2U005MAAS');
    expect(wrapper.text()).toContain('840-00092');
    expect(wrapper.text()).toContain('120 Thùng');
    expect(wrapper.text()).not.toContain('Lưu ý đối chiếu tên hàng!');
  });

  it('displays warning when name_mismatch is true', () => {
    const mismatchResolution: ErroJobOrderResolution = {
      ...sampleResolution,
      name_mismatch: true,
      customer_ref: 'DESC-DIFFERENT',
    };

    const wrapper = mount(ErroJobOrderConfirmModal, {
      props: {
        show: true,
        resolution: mismatchResolution,
        initialPo: '',
        initialLot: '',
      },
    });

    expect(wrapper.text()).toContain('Lưu ý đối chiếu tên hàng!');
    expect(wrapper.text()).toContain('DESC-DIFFERENT');
  });

  it('emits confirm on form submit when valid', async () => {
    const wrapper = mount(ErroJobOrderConfirmModal, {
      props: {
        show: true,
        resolution: sampleResolution,
        initialPo: 'PO-999',
        initialLot: 'LOT-888',
      },
    });

    const form = wrapper.find('form');
    await form.trigger('submit');

    expect(wrapper.emitted('confirm')).toBeTruthy();
    expect(wrapper.emitted('confirm')?.[0]).toEqual([{ po: 'PO-999', lot: 'LOT-888' }]);
  });
});
