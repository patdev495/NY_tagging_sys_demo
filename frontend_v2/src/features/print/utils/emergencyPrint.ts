import type { Carton, Product } from '../../../types/api';

export function resolveCartonTemplatePath(carton: Carton | null | undefined, fallbackProduct?: Product | null): string {
  return carton?.product?.template_path || fallbackProduct?.template_path || '';
}
