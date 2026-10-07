import api from '../../core/api';
import type { ErroJobOrderResolution, JobOrderDetails, JobOrderSlot } from '../../types/api';

export default {
  getJobOrderDetails(jobOrder: string) {
    return api.get<JobOrderDetails>(`/job-orders/${encodeURIComponent(jobOrder)}`);
  },
  getJobOrderSlots(jobOrder: string) {
    return api.get<JobOrderSlot[]>(`/job-orders/${encodeURIComponent(jobOrder)}/slots`);
  },
  resolveErroJobOrder(jobOrder: string) {
    return api.get<ErroJobOrderResolution>('/job-orders/resolve-erro-job-order', {
      params: { job_order: jobOrder },
    });
  },
};

