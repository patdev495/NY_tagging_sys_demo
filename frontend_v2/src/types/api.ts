export interface Customer {
  id: number;
  code: string;
  name: string;
  is_active: boolean;
}

export interface ProductInternalFactoryPartNumber {
  id: number;
  product_id: number;
  customer_id: number;
  internal_factory_part_number: string;
  source_drawing_code: string;
  created_at?: string;
}

export interface Product {
  id: number;
  customer_id: number;
  item_name: string;
  upc?: string;
  packed_qty: number;
  start_part?: string;
  middle_part?: string;
  template_type: 'standard' | 'detailed' | 'erro_01' | 'erro_02' | 'erro_03' | 'erro_04' | 'erro_05';
  template_path?: string;
  allow_partial: number;
  packing_mode?: 'item_scan' | 'weight_scale';
  target_weight?: number;
  min_weight?: number;
  max_weight?: number;
  weight_unit?: string;
  mfr_pn?: string;
  pkg_prefix?: string;
  revision?: string;
  asin?: string;
  product_desc?: string;
  customer_project?: string;
  production_stage?: string;
  luxshare_part_number?: string;
  internal_factory_part_number?: string;
  factory_item_code?: string;
  carton_id_prefix?: 'H' | 'K';
  customer?: Customer;
  internal_factory_part_numbers?: ProductInternalFactoryPartNumber[];
}

export interface Carton {
  id: number;
  carton_sn: string;
  product_sku?: string;
  product_name?: string;
  customer_name?: string;
  packed_qty?: number;
  created_at: string;
  status?: string;
  job_order?: string;
  station_id?: string;
  carton_origin?: string;
  is_reprint?: boolean | number;
  product?: Product;
  items?: { id: number; item_sn: string }[];
  weight?: number;
  po_number?: string;
  lot_number?: string;
  date_code?: string;
  btxml?: string;
  items_count?: number;
  reprint_count?: number;
  print_history?: CartonPrintAttempt[];
}

export interface CartonPrintAttempt {
  carton_sn: string;
  created_at: string;
  status: string;
  is_reprint?: boolean | number;
  items_count?: number;
}

export interface ItemSNConflictCarton {
  id: number;
  carton_sn: string;
  product_name?: string | null;
  job_order?: string | null;
  status?: string | null;
  station_id?: string | null;
  created_at?: string | null;
  items_count: number;
}

export interface ItemSNConflictResponse {
  item_sn: string;
  conflicts: ItemSNConflictCarton[];
}

export interface ScaleReading {
  weight: number;
  weight_str?: string;
  unit: string;
  is_stable: boolean;
  is_tare?: boolean;
  is_net?: boolean;
  is_zero?: boolean;
  is_hold?: boolean;
  connected?: boolean;
  is_streaming?: boolean;
  timestamp?: number;
}


export interface ScaleStatus {
  connected: boolean;
  port: string;
  baudrate: number;
  is_streaming: boolean;
  mock_mode?: boolean;
}

export interface CartonWeighPackPayload {
  product_id: number;
  weight: number;
  job_order?: string;
  po_number?: string;
  lot_number?: string;
  printer_name?: string;
  template_path?: string;
  station_id?: string;
  carton_origin?: string;
  custom_sn?: number;
}


export interface ScanItem {
  sn: string;
  timestamp: string;
}

export interface PrintJobStatus {
  status: 'pending' | 'printing' | 'success' | 'failed';
  message: string;
  carton_sn?: string;
}

export interface JobOrderSlot {
  id: number;
  carton_number: number;
  carton_sn: string;
  status: 'PENDING' | 'SCANNED';
  scanned_at?: string;
  carton_id?: number;
}

export interface JobOrderDetails {
  job_order: string;
  total_qty: number;
  total_cartons: number;
  product: Product;
  slots: JobOrderSlot[];
}

export interface ErroJobOrderResolution {
  job_order: string;
  factory_part_number: string;
  customer_ref: string;
  total_qty: number;
  planned_cartons: number;
  packed_cartons_count: number;
  name_mismatch: boolean;
  lot_number_default?: string | null;
  product: Product;
}
