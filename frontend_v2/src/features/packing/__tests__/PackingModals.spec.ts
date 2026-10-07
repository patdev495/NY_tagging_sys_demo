import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import i18n from '../../../i18n';
import CartonSlotsModal from '../components/CartonSlotsModal.vue';
import CartonVerificationModal from '../components/CartonVerificationModal.vue';
import type { JobOrderSlot, Carton, Product } from '../../../types/api';

describe('Packing Modals', () => {
  it('CartonSlotsModal renders slots and emits select-slot', async () => {
    const slots: JobOrderSlot[] = [
      { id: 1, carton_number: 1, carton_sn: 'CN26081100001', status: 'PENDING' },
      { id: 2, carton_number: 2, carton_sn: 'CN26081100002', status: 'SCANNED' },
    ];

    const wrapper = mount(CartonSlotsModal, {
      props: {
        show: true,
        jobOrder: 'JO-123',
        totalCartons: 2,
        scannedCount: 1,
        slots,
        selectedSlotId: 1,
      },
      global: {
        plugins: [i18n],
      },
    });

    expect(wrapper.text()).toContain('CN26081100001');
    expect(wrapper.text()).toContain('CN26081100002');

    // Click first slot
    const slotItems = wrapper.findAll('.slot-card');
    await slotItems[0].trigger('click');
    expect(wrapper.emitted('selectSlot')?.[0]).toEqual([slots[0]]);

    // Click close
    const closeBtn = wrapper.find('button.bg-blue-600');
    await closeBtn.trigger('click');
    expect(wrapper.emitted('close')).toBeTruthy();
  });

  it('CartonVerificationModal verifies scanned S/N against expected S/N', async () => {
    const mockProduct: Product = {
      id: 1,
      customer_id: 1,
      item_name: 'Test-Product',
      packed_qty: 10,
      template_type: 'standard',
      allow_partial: 0,
    };

    const mockCarton: Carton = {
      id: 10,
      carton_sn: 'CN26081100001',
      job_order: 'JO-123',
      product: mockProduct,
      status: 'PRINTED',
      packed_qty: 10,
      created_at: new Date().toISOString(),
    };

    const wrapper = mount(CartonVerificationModal, {
      props: {
        show: true,
        carton: mockCarton,
        currentProduct: mockProduct,
        scannedCount: 10,
      },
      global: {
        plugins: [i18n],
      },
    });

    expect(wrapper.text()).toContain('CN26081100001');

    const input = wrapper.find('input');

    // Wrong scan
    await input.setValue('WRONG-SN');
    await input.trigger('keydown.enter');
    expect(wrapper.emitted('scanAlert')).toBeTruthy();
    expect(wrapper.emitted('verified')).toBeFalsy();

    // Correct scan
    await input.setValue('CN26081100001');
    await input.trigger('keydown.enter');
    expect(wrapper.emitted('verified')?.[0]).toEqual([mockCarton]);
  });
});
