import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';
import ErroProductCardStep from './ErroProductCardStep.vue';
import type { ErroJobOrderResolution } from '../../../../types/api';

describe('ErroProductCardStep', () => {
  const sampleResolution: ErroJobOrderResolution = {
    job_order: '1259487',
    factory_part_number: '1LAE0091C2U005MAAS',
    customer_ref: '840-00092',
    total_qty: 22800,
    planned_cartons: 120,
    packed_cartons_count: 0,
    name_mismatch: false,
    product: {
      id: 1,
      customer_id: 1,
      customer_name: 'Erro',
      item_name: '840-00092',
      customer_part_number: '840-00092',
      template_type: 'erro_01',
      packed_qty: 190,
      net_weight: 10.0,
      tolerance_percentage: 5.0,
      gross_weight_min: 9.5,
      gross_weight_max: 10.5,
      unit: 'PCS',
    } as any,
  };

  it('renders product details and specs correctly', () => {
    const wrapper = mount(ErroProductCardStep, {
      props: {
        jobOrder: '1259487',
        resolution: sampleResolution,
        initialPo: '',
        initialLot: '',
      },
    });

    expect(wrapper.text()).toContain('1259487');
    expect(wrapper.text()).toContain('1LAE0091C2U005MAAS');
    expect(wrapper.text()).toContain('840-00092');
    expect(wrapper.text()).toContain('120 thùng');
    expect(wrapper.text()).toContain('190 pcs/thùng');
    expect(wrapper.text()).not.toContain('Lưu ý đối chiếu tên hàng!');
  });

  it('displays warning when name_mismatch is true', () => {
    const mismatchResolution: ErroJobOrderResolution = {
      ...sampleResolution,
      name_mismatch: true,
      customer_ref: 'DIFFERENT-DESC-FROM-ERP',
    };

    const wrapper = mount(ErroProductCardStep, {
      props: {
        jobOrder: '1259487',
        resolution: mismatchResolution,
        initialPo: '',
        initialLot: '',
      },
    });

    expect(wrapper.text()).toContain('Lưu ý đối chiếu tên hàng!');
    expect(wrapper.text()).toContain('DIFFERENT-DESC-FROM-ERP');
  });

  it('hides PO/LOT inputs for template erro_02', () => {
    const tem2Resolution: ErroJobOrderResolution = {
      ...sampleResolution,
      product: {
        ...sampleResolution.product,
        template_type: 'erro_02',
      },
    };

    const wrapper = mount(ErroProductCardStep, {
      props: {
        jobOrder: '1259487',
        resolution: tem2Resolution,
        initialPo: '',
        initialLot: '',
      },
    });

    expect(wrapper.text()).toContain('Mẫu tem erro_02 (SSCC) không yêu cầu in PO và LOT');
    expect(wrapper.find('input#batch-po').exists()).toBe(false);
  });

  it('shows LOT as backend-generated for template erro_03', () => {
    const tem3Resolution: ErroJobOrderResolution = {
      ...sampleResolution,
      product: {
        ...sampleResolution.product,
        template_type: 'erro_03',
      },
    };

    const wrapper = mount(ErroProductCardStep, {
      props: {
        jobOrder: '1259487',
        resolution: tem3Resolution,
        initialPo: '',
        initialLot: '',
      },
    });

    const lotInput = wrapper.find<HTMLInputElement>('input#batch-lot');
    expect(lotInput.exists()).toBe(true);
    expect(lotInput.attributes('disabled')).toBeDefined();
    expect(lotInput.attributes('placeholder')).toContain('YYYYMMDD');
  });

  it('shows the generated LOT date beneath the confirmed product', () => {
    const wrapper = mount(ErroProductCardStep, {
      props: {
        jobOrder: '1259487',
        resolution: { ...sampleResolution, lot_number_default: '20260921' },
        initialPo: '',
        initialLot: '20261001',
      },
    });

    expect(wrapper.find<HTMLInputElement>('input#batch-lot').element.value).toBe('20261001');
  });

  it('emits confirm when form submitted with valid inputs', async () => {
    const wrapper = mount(ErroProductCardStep, {
      props: {
        jobOrder: '1259487',
        resolution: sampleResolution,
        initialPo: 'PO-TEST-1',
        initialLot: 'LOT-TEST-1',
      },
    });

    await wrapper.find('form').trigger('submit');

    expect(wrapper.emitted('confirm')).toBeTruthy();
    expect(wrapper.emitted('confirm')?.[0]).toEqual([{ po: 'PO-TEST-1', lot: 'LOT-TEST-1' }]);
  });

  it('emits changeJobOrder when back button is clicked', async () => {
    const wrapper = mount(ErroProductCardStep, {
      props: {
        jobOrder: '1259487',
        resolution: sampleResolution,
        initialPo: '',
        initialLot: '',
      },
    });

    const backButton = wrapper.find('button[type="button"]');
    await backButton.trigger('click');

    expect(wrapper.emitted('changeJobOrder')).toBeTruthy();
  });
});
