import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';

import ErroJobOrderStep from './ErroJobOrderStep.vue';
import jobOrderApi from '../../../job_order/api';

vi.mock('../../../job_order/api', () => ({
  default: {
    resolveErroJobOrder: vi.fn(),
  },
}));

describe('ErroJobOrderStep', () => {
  it('does not allow entry to the packing station until Job Order resolves', async () => {
    vi.mocked(jobOrderApi.resolveErroJobOrder).mockResolvedValue({
      data: {
        job_order: '1259487',
        factory_part_number: '1LAE0091C2U005MAAS',
        customer_ref: '840-00092',
        total_qty: 22800,
        planned_cartons: 120,
        packed_cartons_count: 0,
        name_mismatch: false,
        product: {
          id: 91,
          customer_id: 27,
          item_name: '840-00092',
          packed_qty: 190,
          template_type: 'erro_01',
          allow_partial: 0,
        } as any,
      },
    } as any);

    const wrapper = mount(ErroJobOrderStep);

    expect(wrapper.emitted('resolved')).toBeUndefined();
    await wrapper.get('input').setValue('1259487');
    await wrapper.get('form').trigger('submit');

    expect(jobOrderApi.resolveErroJobOrder).toHaveBeenCalledWith('1259487');
    expect(wrapper.emitted('resolved')?.[0]?.[0]).toMatchObject({
      job_order: '1259487',
      factory_part_number: '1LAE0091C2U005MAAS',
      planned_cartons: 120,
    });
  });

  it('shows an error and keeps the user on the entry step for an invalid Job Order', async () => {
    vi.mocked(jobOrderApi.resolveErroJobOrder).mockRejectedValue({
      response: { data: { error: 'Không thể kết nối cơ sở dữ liệu ShopFloor hoặc công lệnh không hợp lệ.' } },
    });
    const wrapper = mount(ErroJobOrderStep);

    await wrapper.get('input').setValue('9999999');
    await wrapper.get('form').trigger('submit');

    expect(wrapper.emitted('resolved')).toBeUndefined();
    expect(wrapper.text()).toContain('Đã có lỗi xảy ra. Vui lòng thử lại.');
  });
});
