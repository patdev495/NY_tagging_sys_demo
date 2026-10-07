import api from '../../core/api';
import type { Carton, ItemSNConflictResponse } from '../../types/api';

export default {
  createCarton(data: { 
    product_id: number; 
    items: string[]; 
    job_order: string; 
    slot_id: number;
    custom_sn?: number; 
    carton_origin?: string;
    custom_yymm?: string;
  }) {
    return api.post<Carton>('/cartons', data);
  },
  getLastCarton(productId: number, jobOrder?: string) {
    return api.get<Carton>(`/products/${productId}/last-carton`, {
      params: { job_order: jobOrder || undefined },
    });
  },
  getNextSN(productId: number, yymm?: string) {
    return api.get<{ next_seq: number; next_sn?: string | null; prefix?: string }>(`/products/${productId}/next-sn`, { params: { yymm } });
  },
  getItemSNConflicts(itemSN: string, excludeCartonId?: number) {
    return api.get<ItemSNConflictResponse>('/cartons/item-sn-conflicts', {
      params: { item_sn: itemSN, exclude_carton_id: excludeCartonId },
    });
  },
  rescanCarton(data: { carton_sn: string; items: string[] }) {
    return api.put<Carton>('/cartons/rescan', data);
  },
  weighPackCarton(data: import('../../types/api').CartonWeighPackPayload) {
    return api.post<Carton>('/cartons/weigh-pack', data);
  }
};
