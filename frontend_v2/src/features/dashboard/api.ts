import api from '../../core/api';

export interface KPIStats {
  total_cartons: number;
  success_cartons: number;
  failed_cartons: number;
  reprint_cartons: number;
  total_items: number;
  success_rate: number;
  error_rate: number;
  reprint_rate: number;
}

export interface HourlyStat {
  hour: string;
  total: number;
  success: number;
  failed: number;
  total_items: number;
}

export interface ProductStat {
  item_name: string;
  customer_code: string;
  customer_name?: string | null;
  upc?: string | null;
  packed_qty?: number | null;
  count: number;
  total_items: number;
  percentage: number;
}


export interface LiveCartonFeed {
  id: number;
  carton_sn: string;
  item_name: string;
  customer_code: string;
  created_at: string;
  status: string;
  is_reprint: number;
  weight: number | null;
  station_id: string | null;
  items_count: number;
}

export interface SystemHealth {
  bartender_status: 'ready' | 'offline';
  active_printers_count: number;
}

export interface DashboardStatsResponse {
  time_range: string;
  kpis: KPIStats;
  hourly_throughput: HourlyStat[];
  top_products: ProductStat[];
  live_feed: LiveCartonFeed[];
  system: SystemHealth;
}

export type DashboardTimeRange = 'today' | 'yesterday' | '7d' | '30d' | 'custom';

export async function fetchDashboardStats(
  timeRange: DashboardTimeRange = 'today',
  startDate?: string,
  endDate?: string
): Promise<DashboardStatsResponse> {
  const params: Record<string, any> = { time_range: timeRange };
  if (timeRange === 'custom') {
    if (startDate) params.start_date = startDate;
    if (endDate) params.end_date = endDate;
  }
  const response = await api.get<DashboardStatsResponse>('/admin/dashboard/stats', {
    params,
  });
  return response.data;
}
