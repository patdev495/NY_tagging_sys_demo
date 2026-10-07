import { describe, expect, it } from 'vitest';
import { resolveCartonTemplatePath } from '../utils/emergencyPrint';
import type { Carton, Product } from '../../../types/api';

const currentProduct: Product = {
  id: 1,
  customer_id: 1,
  item_name: 'Current scan product',
  packed_qty: 10,
  start_part: 'VN',
  middle_part: '11',
  template_type: 'standard',
  template_path: 'templates/current-product.btw',
  allow_partial: 0,
};

function carton(overrides: Partial<Carton> = {}): Carton {
  return {
    id: 99,
    carton_sn: 'CN26051600001',
    product_sku: '',
    product_name: '',
    customer_name: '',
    packed_qty: 10,
    created_at: '2026-06-16T00:00:00',
    product: {
      ...currentProduct,
      id: 2,
      item_name: 'Emergency reprint product',
      template_path: 'templates/emergency-product.btw',
    },
    ...overrides,
  };
}

describe('resolveCartonTemplatePath', () => {
  it('uses the carton product template for emergency reprint while another product is being scanned', () => {
    expect(resolveCartonTemplatePath(carton(), currentProduct)).toBe('templates/emergency-product.btw');
  });

  it('falls back to the active product for normal in-session printing', () => {
    expect(resolveCartonTemplatePath(null, currentProduct)).toBe('templates/current-product.btw');
  });

  it('does not invent a template before any job order is loaded', () => {
    expect(resolveCartonTemplatePath(carton({ product: undefined }), null)).toBe('');
  });
});
