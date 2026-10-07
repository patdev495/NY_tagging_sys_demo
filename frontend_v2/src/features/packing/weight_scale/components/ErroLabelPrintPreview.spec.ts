import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import ErroLabelPrintPreview from './ErroLabelPrintPreview.vue';
import type { Product } from '../../../../types/api';

describe('ErroLabelPrintPreview', () => {
  it('shows all Erro 02 print values, including SSCC check digit, for pre-print verification', () => {
    const product: Product = {
      id: 2,
      customer_id: 1,
      item_name: 'G012C1B',
      packed_qty: 190,
      template_type: 'erro_02',
      allow_partial: 0,
      product_desc: 'ASSY, BAND WRAPPED, CAT5E ETHERNET CABLE',
      mfr_pn: 'NYS5998',
      asin: 'B08G9M4HXS',
      upc: '852582006785',
    };

    const wrapper = mount(ErroLabelPrintPreview, {
      props: {
        product,
        cartonSN: '03703390700000017',
        po: '',
        lot: '',
        now: new Date('2026-09-15T08:00:00'),
      },
    });

    expect(wrapper.text()).toContain('Product name:ASSY, BAND WRAPPED, CAT5E ETHERNET CABLE');
    expect(wrapper.text()).toContain('(00) 0 37033907 0000001');
    expect(wrapper.text()).toContain('7');
    expect(wrapper.text()).toContain('NYS5998');
    expect(wrapper.text()).toContain('B08G9M4HXS');
    expect(wrapper.text()).toContain('852582006785');
    expect(wrapper.find('[data-testid="preview-errors"]').exists()).toBe(false);
  });

  it('calculates the check digit when the next SSCC is already formatted for display', () => {
    const product: Product = { id: 2, customer_id: 1, item_name: 'G012C1B', packed_qty: 190, template_type: 'erro_02', allow_partial: 0, product_desc: 'Cable', mfr_pn: 'NYS5998', asin: 'B08G9M4HXS', upc: '852582006785' };
    const wrapper = mount(ErroLabelPrintPreview, {
      props: { product, cartonSN: '(00) 0 37033907 0000001', po: '', lot: '', now: new Date('2026-09-15T08:00:00') },
    });

    expect(wrapper.text()).toContain('Check Digit3');
  });

  it('lists missing required Erro 04 fields so the station can block printing', () => {
    const product: Product = {
      id: 4,
      customer_id: 1,
      item_name: '115-00020',
      packed_qty: 120,
      template_type: 'erro_04',
      allow_partial: 0,
      mfr_pn: 'NYS5896',
      carton_id_prefix: 'H',
    };

    const wrapper = mount(ErroLabelPrintPreview, {
      props: {
        product,
        cartonSN: 'H69C000A',
        po: '',
        lot: 'LOT-01',
        now: new Date('2026-09-15T08:00:00'),
      },
    });

    expect(wrapper.find('[data-testid="preview-errors"]').text()).toContain('UPC');
    expect(wrapper.find('[data-testid="preview-errors"]').text()).toContain('PO Number');
    expect(wrapper.find('[data-testid="preview-errors"]').text()).toContain('Revision');
    expect(wrapper.find('[data-testid="preview-errors"]').text()).toContain('SKU Description');
    expect(wrapper.emitted('validation-change')?.[0]).toEqual([["UPC", "PO Number", "Revision", "SKU Description"]]);
  });

  it('derives Erro 05 date and lot codes for the simulated next label', () => {
    const product: Product = {
      id: 5,
      customer_id: 1,
      item_name: '1414-0GDA0BV',
      packed_qty: 1000,
      template_type: 'erro_05',
      allow_partial: 0,
      product_desc: 'X LED CABLE 30AWG 230mm',
    };
    const wrapper = mount(ErroLabelPrintPreview, {
      props: { product, cartonSN: 'MC220TW12263850001', po: '', lot: '', now: new Date('2026-09-15T08:00:00') },
    });

    expect(wrapper.text()).toContain('MC220TW12263850001');
    expect(wrapper.text()).toContain('2638');
    expect(wrapper.text()).toContain('20260915');
    expect(wrapper.find('[data-testid="preview-errors"]').exists()).toBe(false);
  });

  it('renders Erro 01 preview values with ISO week date code YYWW', () => {
    const product: Product = {
      id: 1,
      customer_id: 1,
      item_name: '840-00092',
      packed_qty: 190,
      template_type: 'erro_01',
      allow_partial: 0,
      mfr_pn: 'NYS5998',
      revision: 'B',
    };

    const wrapper = mount(ErroLabelPrintPreview, {
      props: {
        product,
        cartonSN: 'VHK00102372609000001',
        po: 'PO-1234',
        lot: 'LOT-5678',
        now: new Date('2026-09-16T10:00:00'),
      },
    });

    expect(wrapper.text()).toContain('840-00092');
    expect(wrapper.text()).toContain('190');
    expect(wrapper.text()).toContain('NYS5998');
    expect(wrapper.text()).toContain('2638');
    expect(wrapper.text()).toContain('PO-1234');
    expect(wrapper.text()).toContain('LOT-5678');
    expect(wrapper.text()).toContain('VHK00102372609000001');
    expect(wrapper.text()).toContain('MADE IN VIETNAM');
  });

  it('uses the preview date as the automatic LOT when no session LOT is present', () => {
    const product: Product = {
      id: 1, customer_id: 1, item_name: '840-00092', packed_qty: 190,
      template_type: 'erro_01', allow_partial: 0, mfr_pn: 'NYS5998', revision: 'B',
    };
    const wrapper = mount(ErroLabelPrintPreview, {
      props: {
        product, cartonSN: 'VHK00102372610000014', po: 'PO-1', lot: '',
        now: new Date('2026-10-01T10:00:00'),
      },
    });

    expect(wrapper.text()).toContain('20261001');
    expect(wrapper.find('[data-testid="preview-errors"]').exists()).toBe(false);
  });
});
