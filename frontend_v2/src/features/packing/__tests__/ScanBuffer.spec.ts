import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import i18n from '../../../i18n';
import ScanBuffer from '../components/ScanBuffer.vue';

describe('ScanBuffer.vue', () => {
  const defaultProps = {
    scanBuffer: '',
    jobOrder: 'JO-2026-001',
    awaitingNext: false,
    invalidScans: [],
    overflowScans: [],
    allowPartial: false,
    scannedCount: 0,
    disabled: false,
    placeholder: 'Bắn mã sê-ri con (Item SN) vào đây...',
  };

  it('renders input as enabled when awaitingNext is false and disabled is false', () => {
    const wrapper = mount(ScanBuffer, {
      props: defaultProps,
      global: { plugins: [i18n] },
    });

    const input = wrapper.find('input');
    expect(input.attributes('disabled')).toBeUndefined();
    expect(wrapper.text()).toContain('SẴN SÀNG QUÉT MÃ');
    expect(wrapper.find('button').exists()).toBe(false);
  });

  it('emits scan event when Enter is pressed and input is enabled', async () => {
    const wrapper = mount(ScanBuffer, {
      props: { ...defaultProps, scanBuffer: 'SN12345' },
      global: { plugins: [i18n] },
    });

    const input = wrapper.find('input');
    await input.trigger('keydown.enter');
    expect(wrapper.emitted('scan')).toHaveLength(1);
  });

  it('disables input and shows next carton button when awaitingNext is true', () => {
    const wrapper = mount(ScanBuffer, {
      props: { ...defaultProps, awaitingNext: true },
      global: { plugins: [i18n] },
    });

    const input = wrapper.find('input');
    expect(input.attributes('disabled')).toBeDefined();
    expect(input.attributes('placeholder')).toContain('ĐÃ ĐÓNG THÙNG');
    expect(wrapper.text()).toContain('TẠM KHÓA — CHỜ ĐỔI THÙNG');

    const nextBtn = wrapper.find('button');
    expect(nextBtn.exists()).toBe(true);
    expect(nextBtn.text()).toContain('Thùng Tiếp Theo');
  });

  it('emits next-carton when clicking Next Carton button in awaitingNext state', async () => {
    const wrapper = mount(ScanBuffer, {
      props: { ...defaultProps, awaitingNext: true },
      global: { plugins: [i18n] },
    });

    const nextBtn = wrapper.find('button');
    await nextBtn.trigger('click');
    expect(wrapper.emitted('next-carton')).toHaveLength(1);
  });

  it('emits next-carton on global Space keydown when awaitingNext is true without errors', async () => {
    const wrapper = mount(ScanBuffer, {
      props: { ...defaultProps, awaitingNext: true },
      global: { plugins: [i18n] },
      attachTo: document.body,
    });

    const spaceEvent = new KeyboardEvent('keydown', { code: 'Space', key: ' ', bubbles: true });
    window.dispatchEvent(spaceEvent);

    expect(wrapper.emitted('next-carton')).toHaveLength(1);
    wrapper.unmount();
  });

  it('does NOT emit next-carton on Space or button click when errors exist', async () => {
    const wrapper = mount(ScanBuffer, {
      props: {
        ...defaultProps,
        awaitingNext: true,
        invalidScans: [{ sn: 'ERR1', time: '12:00', reason: 'Invalid' }],
      },
      global: { plugins: [i18n] },
      attachTo: document.body,
    });

    const nextBtn = wrapper.find('button');
    expect(nextBtn.attributes('disabled')).toBeDefined();

    await nextBtn.trigger('click');
    expect(wrapper.emitted('next-carton')).toBeUndefined();

    const spaceEvent = new KeyboardEvent('keydown', { code: 'Space', key: ' ', bubbles: true });
    window.dispatchEvent(spaceEvent);
    expect(wrapper.emitted('next-carton')).toBeUndefined();

    wrapper.unmount();
  });
});
