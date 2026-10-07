import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import ErroStepperBar from './ErroStepperBar.vue';

describe('ErroStepperBar', () => {
  it('highlights step 1 when currentStep is 1', () => {
    const wrapper = mount(ErroStepperBar, {
      props: {
        currentStep: 1,
      },
    });

    expect(wrapper.text()).toContain('1. Nhập Công Lệnh');
    expect(wrapper.text()).toContain('2. Xác Nhận Đơn Hàng');
    expect(wrapper.text()).toContain('3. Cân & Đóng Thùng');
    expect(wrapper.text()).not.toContain('Công Lệnh:');
  });

  it('highlights step 2 and displays job order info when currentStep is 2', () => {
    const wrapper = mount(ErroStepperBar, {
      props: {
        currentStep: 2,
        jobOrder: 'WO-12345',
        factoryPartNumber: '1LAE0091',
        productItemName: '840-00092',
      },
    });

    expect(wrapper.text()).toContain('WO-12345');
    expect(wrapper.text()).toContain('1LAE0091');
    expect(wrapper.text()).toContain('840-00092');
  });

  it('highlights step 3 and displays job order info when currentStep is 3', () => {
    const wrapper = mount(ErroStepperBar, {
      props: {
        currentStep: 3,
        jobOrder: 'WO-12345',
        factoryPartNumber: '1LAE0091',
        productItemName: '840-00092',
      },
    });

    expect(wrapper.text()).toContain('WO-12345');
    expect(wrapper.text()).toContain('840-00092');
  });
});
