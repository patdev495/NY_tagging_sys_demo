import api from '../../core/api';

export interface JobOrderSummary {
  job_order: string;
  product_id: number;
  product_name: string;
  customer_code: string;
  total_slots: number;
  scanned_slots: number;
  pending_slots: number;
  shipped_slots: number;
  completion_rate: number;
  latest_scan_at: string | null;
}

export interface JobOrderSlotDetail {
  id: number;
  carton_number: number;
  carton_sn: string;
  status: 'PENDING' | 'SCANNED';
  scanned_at: string | null;
  carton_id: number | null;
  shipped: number;
}

export interface JobOrderSlotCancellationCheck {
  job_order: string;
  total_slots: number;
  scanned_slots: number;
  can_cancel: boolean;
}

export interface JobOrderSlotCancellationResult {
  job_order: string;
  deleted_slots: number;
}

export interface POLotRunSummary {
  po_number: string;
  lot_number: string;
  product_name: string;
  customer_code: string;
  date_code: string | null;
  total_cartons: number;
  total_weight: number;
  latest_packed_at: string | null;
}

export async function fetchJobOrdersSummary(): Promise<JobOrderSummary[]> {
  const response = await api.get<JobOrderSummary[]>('/admin/production-runs/job-orders');
  return response.data;
}

export async function fetchJobOrderSlots(jobOrder: string): Promise<JobOrderSlotDetail[]> {
  const response = await api.get<JobOrderSlotDetail[]>(`/admin/production-runs/job-orders/${encodeURIComponent(jobOrder)}/slots`);
  return response.data;
}

export async function checkJobOrderSlotCancellation(jobOrder: string): Promise<JobOrderSlotCancellationCheck> {
  const response = await api.get<JobOrderSlotCancellationCheck>(
    `/admin/production-runs/job-orders/${encodeURIComponent(jobOrder)}/cancellation-check`,
  );
  return response.data;
}

export async function cancelJobOrderSlotAllocation(jobOrder: string): Promise<JobOrderSlotCancellationResult> {
  const response = await api.delete<JobOrderSlotCancellationResult>(
    `/admin/production-runs/job-orders/${encodeURIComponent(jobOrder)}/slots`,
  );
  return response.data;
}

export async function fetchPOLotRuns(): Promise<POLotRunSummary[]> {
  const response = await api.get<POLotRunSummary[]>('/admin/production-runs/po-runs');
  return response.data;
}
