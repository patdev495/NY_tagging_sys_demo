import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import ErroProductSelectModal from './ErroProductSelectModal.vue';
import type { Product } from '../../../../types/api';


describe('ErroProductSelectModal', () => {
  it('groups an Erro 04 Product as PD027032 and emits it when selected', async () => {
    const erro04: Product = {
      id: 4,
      customer_id: 1,
      item_name: 'G111A1A',
      packed_qty: 120,
      template_type: 'erro_04',
      allow_partial: 0,
      mfr_pn: 'NYS5896',
      carton_id_prefix: 'H',
      min_weight: 0,
      max_weight: 10,
    };

    const wrapper = mount(ErroProductSelectModal, {
      props: {
        show: true,
        products: [erro04],
        selectedProduct: null,
      },
    });

    expect(wrapper.text()).toContain('Erro 04 · PD027032');
    await wrapper.findAll('button').find(button => button.text().includes('G111A1A'))!.trigger('click');
    expect(wrapper.emitted('select')?.[0]).toEqual([erro04]);
  });
});
