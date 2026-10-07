import { flushPromises, mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import i18n from '../../i18n';
import { useAuthStore } from '../../core/stores/auth';
import { checkJobOrderSlotCancellation } from '../../features/production_run/api';
import ProductionRunsPage from './ProductionRunsPage.vue';

vi.mock('../../features/production_run/api', () => ({
  fetchJobOrdersSummary: vi.fn().mockResolvedValue([]),
  fetchJobOrderSlots: vi.fn().mockResolvedValue([]),
  fetchPOLotRuns: vi.fn().mockResolvedValue([]),
  checkJobOrderSlotCancellation: vi.fn(),
  cancelJobOrderSlotAllocation: vi.fn(),
}));

describe('ProductionRunsPage', () => {
  let pinia: ReturnType<typeof createPinia>;

  beforeEach(() => {
    pinia = createPinia();
    setActivePinia(pinia);
    const auth = useAuthStore(pinia);
    auth.user = { id: 1, username: 'admin', role: 'admin' };
  });

  it('lets an Admin open the Job Order slot allocation cancellation check', async () => {
    const wrapper = mount(ProductionRunsPage, {
      global: { plugins: [i18n, pinia] },
    });
    await flushPromises();

    await wrapper.get('[data-testid="open-slot-cancellation"]').trigger('click');

    expect(wrapper.text()).toContain('Kiểm tra huỷ cấp phát');
    expect(wrapper.get('[data-testid="cancellation-job-order-input"]').exists()).toBe(true);
  });

  it('only exposes confirmation after an unscanned slot allocation passes the check', async () => {
    vi.mocked(checkJobOrderSlotCancellation).mockResolvedValue({
      job_order: '1257157', total_slots: 2, scanned_slots: 0, can_cancel: true,
    });
    const wrapper = mount(ProductionRunsPage, {
      global: { plugins: [i18n, pinia] },
    });
    await flushPromises();

    await wrapper.get('[data-testid="open-slot-cancellation"]').trigger('click');
    await wrapper.get('[data-testid="cancellation-job-order-input"]').setValue('1257157');
    await wrapper.get('[data-testid="check-slot-cancellation"]').trigger('click');
    await flushPromises();

    expect(wrapper.text()).toContain('Slot đã cấp');
    expect(wrapper.text()).toContain('2');
    expect(wrapper.get('[data-testid="confirm-slot-cancellation"]').text()).toContain('Xác nhận xoá 2 slot');
  });
});
