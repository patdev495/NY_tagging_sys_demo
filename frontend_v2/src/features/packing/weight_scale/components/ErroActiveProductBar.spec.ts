import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import ErroActiveProductBar from './ErroActiveProductBar.vue';
import type { Product } from '../../../../types/api';

describe('ErroActiveProductBar', () => {
  const sampleProduct: Product = {
    id: 1,
    customer_id: 1,
    item_name: '840-00092',
    template_type: 'erro_01',
    packed_qty: 190,
    allow_partial: 0,
  };

  it('renders job order, CPN and carton progress', () => {
    const wrapper = mount(ErroActiveProductBar, {
      props: {
        activeJobOrder: 'WO-12345',
        activeFactoryPartNumber: '1LAE0091',
        selectedProduct: sampleProduct,
        jobOrderPlannedCartons: 100,
        jobOrderPackedCartonsCount: 25,
        jobOrderTotalQty: 19000,
        activePO: 'PO-TEST',
        activeLot: 'LOT-TEST',
        isOpeningTemplate: false,
      },
    });

    expect(wrapper.text()).toContain('WO-12345');
    expect(wrapper.text()).toContain('1LAE0091');
    expect(wrapper.text()).toContain('840-00092');
    expect(wrapper.text()).toContain('25 / 100 thùng');
    expect(wrapper.text()).toContain('PO: PO-TEST');
    expect(wrapper.text()).toContain('LOT: LOT-TEST');
  });

  it('emits openTemplate, editBatch, changeJobOrder, showCartons events', async () => {
    const wrapper = mount(ErroActiveProductBar, {
      props: {
        activeJobOrder: 'WO-12345',
        activeFactoryPartNumber: '1LAE0091',
        selectedProduct: sampleProduct,
        jobOrderPlannedCartons: 100,
        jobOrderPackedCartonsCount: 25,
        jobOrderTotalQty: 19000,
        activePO: 'PO-TEST',
        activeLot: 'LOT-TEST',
        isOpeningTemplate: false,
      },
    });

    // Click Mở Mẫu Tem
    const openBtn = wrapper.findAll('button').find(b => b.text().includes('Mở Mẫu Tem'));
    await openBtn?.trigger('click');
    expect(wrapper.emitted('openTemplate')).toBeTruthy();

    // Click Đổi PO/LOT
    const editBatchBtn = wrapper.findAll('button').find(b => b.text().includes('Đổi PO/LOT'));
    await editBatchBtn?.trigger('click');
    expect(wrapper.emitted('editBatch')).toBeTruthy();

    // Click Đổi Công Lệnh
    const changeJobOrderBtn = wrapper.findAll('button').find(b => b.text().includes('Đổi Công Lệnh'));
    await changeJobOrderBtn?.trigger('click');
    expect(wrapper.emitted('changeJobOrder')).toBeTruthy();

    // Click Progress button
    const progressBtn = wrapper.findAll('button').find(b => b.text().includes('25 / 100 thùng'));
    await progressBtn?.trigger('click');
    expect(wrapper.emitted('showCartons')).toBeTruthy();
  });
});
