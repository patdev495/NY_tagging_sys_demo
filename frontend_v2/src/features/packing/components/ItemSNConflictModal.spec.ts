import { flushPromises, mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';

import ItemSNConflictModal from './ItemSNConflictModal.vue';
import historyApi from '../../history/api';

vi.mock('../../history/api', () => ({
  default: { getCartonDetail: vi.fn() },
}));

describe('ItemSNConflictModal', () => {
  it('shows a read-only conflict summary and loads item details only when requested', async () => {
    vi.mocked(historyApi.getCartonDetail).mockResolvedValue({
      data: { items: [{ id: 1, item_sn: 'ITEM-DUP' }, { id: 2, item_sn: 'ITEM-OTHER' }] },
    } as never);

    const wrapper = mount(ItemSNConflictModal, {
      props: {
        show: true,
        conflict: {
          item_sn: 'ITEM-DUP',
          conflicts: [{
            id: 10,
            carton_sn: 'UI-001',
            product_name: 'UI Cable',
            job_order: 'JO-1',
            status: 'SUCCESS',
            station_id: 'ST-01',
            created_at: '2026-09-29T10:00:00',
            items_count: 2,
          }],
        },
      },
    });

    expect(wrapper.text()).toContain('ITEM-DUP');
    expect(wrapper.text()).toContain('UI-001');
    expect(historyApi.getCartonDetail).not.toHaveBeenCalled();

    await wrapper.get('button.text-blue-700').trigger('click');
    await flushPromises();

    expect(historyApi.getCartonDetail).toHaveBeenCalledWith(10);
    expect(wrapper.text()).toContain('ITEM-OTHER');
    expect(wrapper.text()).not.toContain('Quét lại');
  });
});
