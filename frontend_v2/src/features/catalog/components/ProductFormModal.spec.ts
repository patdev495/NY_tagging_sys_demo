import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import ProductFormModal from './ProductFormModal.vue';
import type { Customer, Product } from '../../../types/api';

vi.mock('../../print/api', () => ({
  default: {
    getTemplates: vi.fn().mockResolvedValue({ data: { templates: [] } }),
    whoami: vi.fn().mockResolvedValue({ data: { ip: '127.0.0.1' } }),
  },
}));

describe('ProductFormModal', () => {
  beforeEach(() => setActivePinia(createPinia()));

  it('lets an admin edit Customer Project and Production Stage for an Erro 03 Product', () => {
    const erro: Customer = { id: 1, code: 'ERRO', name: 'Erro', is_active: true };
    const product: Product = {
      id: 3,
      customer_id: erro.id,
      item_name: '2M21-00508-0004H',
      packed_qty: 190,
      template_type: 'erro_03',
      allow_partial: 0,
      packing_mode: 'weight_scale',
      luxshare_part_number: 'LLERJ014-NC-R',
      customer_project: 'Andy Town/ Firefly',
      production_stage: 'MP',
    };

    const wrapper = mount(ProductFormModal, {
      props: { show: true, isEdit: true, isSubmitting: false, customers: [erro], initialData: product },
    });

    expect(wrapper.text()).toContain('Customer Project *');
    expect(wrapper.text()).toContain('Production Stage *');
    expect(wrapper.text()).toContain('Mã Liệu Luxshare *');
    expect((wrapper.find('input[placeholder="LLERJ014-NC-R"]').element as HTMLInputElement).value)
      .toBe('LLERJ014-NC-R');
    expect((wrapper.find('input[placeholder="Andy Town/ Firefly"]').element as HTMLInputElement).value)
      .toBe('Andy Town/ Firefly');
    expect((wrapper.find('input[placeholder="MP"]').element as HTMLInputElement).value).toBe('MP');
  });
});
