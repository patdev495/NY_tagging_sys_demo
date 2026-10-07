import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';

import ErroFactoryPartNumberLookup from './ErroFactoryPartNumberLookup.vue';
import catalogApi from '../../../catalog/api';

vi.mock('../../../catalog/api', () => ({
  default: {
    resolveErroProductByInternalFactoryPartNumber: vi.fn(),
  },
}));

describe('ErroFactoryPartNumberLookup', () => {
  it('resolves a Factory P/N and emits the locked Product for the packing station', async () => {
    vi.mocked(catalogApi.resolveErroProductByInternalFactoryPartNumber).mockResolvedValue({
      data: {
        id: 12,
        customer_id: 1,
        item_name: 'G012C1B',
        internal_factory_part_number: '1LAE0009D2U004MAAR',
        packed_qty: 190,
        template_type: 'erro_02',
        allow_partial: 0,
      },
    } as any);
    const wrapper = mount(ErroFactoryPartNumberLookup);

    await wrapper.get('input').setValue('1lae0009d2u004maar');
    await wrapper.get('form').trigger('submit');

    expect(wrapper.emitted('resolved')?.[0]?.[0]).toMatchObject({
      id: 12,
      template_type: 'erro_02',
      internal_factory_part_number: '1LAE0009D2U004MAAR',
    });
    expect(wrapper.text()).toContain('G012C1B');
  });

  it('keeps the station unselected and shows an error for an unconfigured Factory P/N', async () => {
    vi.mocked(catalogApi.resolveErroProductByInternalFactoryPartNumber).mockRejectedValue({
      response: { data: { error: 'Factory P/N chưa được cấu hình cho khách hàng Erro.' } },
    });
    const wrapper = mount(ErroFactoryPartNumberLookup);

    await wrapper.get('input').setValue('1LAEUNKNOWN');
    await wrapper.get('form').trigger('submit');

    expect(wrapper.emitted('resolved')).toBeUndefined();
    expect(wrapper.text()).toContain('Đã có lỗi xảy ra. Vui lòng thử lại.');
  });
});
