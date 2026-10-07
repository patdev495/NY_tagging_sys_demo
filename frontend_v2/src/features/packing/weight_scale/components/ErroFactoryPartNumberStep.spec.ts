import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';

import ErroFactoryPartNumberStep from './ErroFactoryPartNumberStep.vue';
import catalogApi from '../../../catalog/api';

vi.mock('../../../catalog/api', () => ({
  default: {
    resolveErroProductByInternalFactoryPartNumber: vi.fn(),
  },
}));

describe('ErroFactoryPartNumberStep', () => {
  it('does not allow entry to the packing station until Factory P/N resolves', async () => {
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
    const wrapper = mount(ErroFactoryPartNumberStep);

    expect(wrapper.emitted('resolved')).toBeUndefined();
    await wrapper.get('input').setValue('1lae0009d2u004maar');
    await wrapper.get('form').trigger('submit');

    expect(catalogApi.resolveErroProductByInternalFactoryPartNumber).toHaveBeenCalledWith('1lae0009d2u004maar');
    expect(wrapper.emitted('resolved')?.[0]?.[0]).toMatchObject({
      id: 12,
      internal_factory_part_number: '1LAE0009D2U004MAAR',
    });
  });

  it('shows an error and keeps the user on the entry step for an unknown Factory P/N', async () => {
    vi.mocked(catalogApi.resolveErroProductByInternalFactoryPartNumber).mockRejectedValue({
      response: { data: { detail: 'Factory P/N chưa được cấu hình cho khách hàng Erro.' } },
    });
    const wrapper = mount(ErroFactoryPartNumberStep);

    await wrapper.get('input').setValue('1LAEUNKNOWN');
    await wrapper.get('form').trigger('submit');

    expect(wrapper.emitted('resolved')).toBeUndefined();
    expect(wrapper.text()).toContain('Đã có lỗi xảy ra. Vui lòng thử lại.');
  });
});
