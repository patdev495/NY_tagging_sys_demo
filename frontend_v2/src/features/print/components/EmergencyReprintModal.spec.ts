import { createPinia } from 'pinia';
import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';
import { nextTick } from 'vue';
import i18n from '../../../i18n';
import EmergencyReprintModal from './EmergencyReprintModal.vue';

describe('EmergencyReprintModal', () => {
  async function mountWithCustomer(customerCode: string) {
    const wrapper = mount(EmergencyReprintModal, {
      props: { show: true },
      global: { plugins: [createPinia(), i18n] },
    });

    (wrapper.vm as any).result = {
      id: 1,
      carton_sn: 'CN260900001',
      created_at: '2026-09-15T00:00:00Z',
      product: {
        packing_mode: 'item_scan',
        item_name: 'Test product',
        customer: { code: customerCode },
      },
    };
    await nextTick();

    return wrapper;
  }

  it('offers a station-level reprint action for UI cartons', async () => {
    const wrapper = await mountWithCustomer('UI');

    await wrapper.get('button.bg-slate-900').trigger('click');
    expect(wrapper.emitted('reprint')?.[0]?.[0]).toMatchObject({ carton_sn: 'CN260900001' });
  });

  it('disables a UI reprint while a prior request is in progress', async () => {
    const wrapper = await mountWithCustomer('UI');

    await wrapper.setProps({ isReprinting: true });
    expect(wrapper.get('button.bg-slate-900').attributes('disabled')).toBeDefined();
  });

  it('does not offer a station-level reprint action for ERRO cartons', async () => {
    const wrapper = await mountWithCustomer('ERRO');

    expect(wrapper.text()).not.toContain('In nhãn');
    expect(wrapper.text()).toContain('Admin');
    expect(wrapper.emitted('reprint')).toBeUndefined();
  });

  it('shows every reprint in the returned print history', async () => {
    const wrapper = await mountWithCustomer('UI');
    (wrapper.vm as any).result.print_history = [
      { carton_sn: 'CN260900001', created_at: '2026-09-15T01:00:00Z', status: 'SUCCESS', is_reprint: 1 },
      { carton_sn: 'CN260900001', created_at: '2026-09-15T02:00:00Z', status: 'SUCCESS', is_reprint: 1 },
    ];
    await nextTick();

    expect(wrapper.get('[aria-label="Lịch sử in lại"]').text()).toContain('In lại');
    expect(wrapper.get('[aria-label="Lịch sử in lại"]').findAll('li')).toHaveLength(2);
  });
});
