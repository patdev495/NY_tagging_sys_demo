import api from '../../core/api';
import type { Carton } from '../../types/api';

export default {
  getCartons(params: Record<string, any> = {}) {
    return api.get<{ items: Carton[]; total: number }>('/cartons', { params });
  },
  getCartonDetail(id: number) {
    return api.get<Carton>(`/cartons/${id}`);
  },
  searchByCartonSN(sn: string) {
    return api.get<Carton>('/cartons/search', { params: { carton_sn: sn } });
  },
  searchByItemSN(sn: string) {
    return api.get<Carton>('/cartons/search/item', { params: { item_sn: sn } });
  },
  deleteCarton(id: number) {
    return api.delete(`/cartons/${id}`);
  },
  exportCartons(params: Record<string, any> = {}, mode: 'summary' | 'detailed' = 'summary') {
    return api.get('/cartons/export', {
      params: { ...params, mode },
      responseType: 'blob'
    });
  }
};
