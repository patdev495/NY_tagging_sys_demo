import { ref, computed, watch, type Ref } from 'vue';
import { useSystemStore } from '../../../core/stores/system';
import printApi from '../../print/api';
import type { Customer, Product } from '../../../types/api';

export interface ProductFormData {
  item_name: string;
  upc: string;
  packed_qty: number;
  start_part: string;
  middle_part: string;
  template_type: 'standard' | 'detailed' | 'erro_01' | 'erro_02' | 'erro_03' | 'erro_04' | 'erro_05';
  template_path: string;
  allow_partial: number;
  customer_id: number | null;
  packing_mode: 'item_scan' | 'weight_scale';
  target_weight?: number | null;
  min_weight: number | null;
  max_weight: number | null;
  weight_unit: string;
  mfr_pn: string;
  pkg_prefix: string;
  revision: string;
  asin?: string;
  product_desc?: string;
  customer_project?: string;
  production_stage?: string;
  luxshare_part_number?: string;
  internal_factory_part_number?: string;
  factory_item_code?: string;
  carton_id_prefix?: 'H' | 'K' | '';
}

export interface UseProductFormProps {
  show: boolean;
  isEdit: boolean;
  customers: Customer[];
  initialData?: Product | null;
}

export const UI_TEMPLATES = [
  { filename: 'carton_base.btw', label: 'carton_base.btw (Thùng Tiêu Chuẩn Patch Cords)' },
  { filename: 'Carton_45.btw', label: 'Carton_45.btw (Thùng Cáp Dài 4.5M/5M/8M Đen)' },
  { filename: 'carton_detail_1M_W.btw', label: 'carton_detail_1M_W.btw (Chi Tiết Cáp 1M - Lưới 40 S/N)' },
  { filename: 'carton_detail_2_3M_W.btw', label: 'carton_detail_2_3M_W.btw (Chi Tiết Cáp 2M & 3M - Lưới 40 S/N)' },
  { filename: 'carton_detail_UISP_Connector_SHD.btw', label: 'carton_detail_UISP_Connector_SHD.btw (Chi Tiết UISP Connector)' },
];

export function getCanonicalTemplateName(templateType?: string): string {
  switch (templateType) {
    case 'erro_05': return 'erro_05.btw';
    case 'erro_04': return 'erro_04.btw';
    case 'erro_03': return 'erro_03.btw';
    case 'erro_02': return 'erro_02.btw';
    case 'erro_01': return 'erro_01.btw';
    case 'detailed': return 'carton_detail_1M_W.btw';
    case 'standard':
    default: return 'carton_base.btw';
  }
}

export function useProductForm(
  props: UseProductFormProps | Ref<UseProductFormProps>,
  emit: (e: 'submit', data: ProductFormData) => void
) {
  const system = useSystemStore();

  const availableTemplates = ref<{ name: string; path: string; size_bytes: number; updated_at: string }[]>([]);
  const isValidating = ref<boolean>(false);
  const validationStatus = ref<{ valid: boolean; message: string } | null>(null);

  const getBaseName = (pathStr: string) => {
    if (!pathStr) return '';
    return pathStr.split(/[/\\]/).pop() || pathStr;
  };

  const formatBytes = (bytes: number) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
  };

  const loadTemplates = async () => {
    try {
      const res = await printApi.getTemplates();
      availableTemplates.value = res.data.templates || [];
    } catch (err) {
      console.warn('Could not load BarTender templates:', err);
    }
  };

  const formData = ref<ProductFormData>({
    item_name: '',
    upc: '',
    packed_qty: 1,
    start_part: 'VN',
    middle_part: '',
    template_type: 'standard',
    template_path: '',
    allow_partial: 0,
    customer_id: null,
    packing_mode: 'item_scan',
    target_weight: null,
    min_weight: 12.300,
    max_weight: 12.700,
    weight_unit: 'kg',
    mfr_pn: 'NYS5998',
    pkg_prefix: 'VHK0010237',
    revision: 'B',
    asin: '',
    product_desc: '',
    customer_project: '',
    production_stage: '',
    luxshare_part_number: '',
    internal_factory_part_number: '',
    factory_item_code: '',
    carton_id_prefix: '',
  });

  const checkTemplateValidity = async () => {
    const filename = getBaseName(formData.value.template_path || getCanonicalTemplateName(formData.value.template_type));
    isValidating.value = true;
    validationStatus.value = null;
    try {
      const res = await printApi.validateTemplate(filename);
      validationStatus.value = {
        valid: res.data.valid,
        message: res.data.message
      };
      if (res.data.valid) {
        system.showNotification('Mẫu tem hợp lệ trên BarTender Engine!', 'success');
      } else {
        system.showNotification(`Mẫu tem không hợp lệ: ${res.data.message}`, 'error');
      }
    } catch (err: any) {
      validationStatus.value = {
        valid: false,
        message: err.message || 'Lỗi kiểm tra mẫu tem'
      };
      system.showNotification('Không thể kết nối để kiểm tra mẫu tem', 'error');
    } finally {
      isValidating.value = false;
    }
  };

  const onCustomerChange = () => {
    const currentProps = 'value' in props ? props.value : props;
    if (currentProps.isEdit) return;
    const selectedCust = currentProps.customers.find(c => c.id === formData.value.customer_id);
    if (!selectedCust) return;

    const code = (selectedCust.code || '').toUpperCase();
    if (code === 'ERRO') {
      formData.value.packing_mode = 'weight_scale';
      formData.value.template_type = 'erro_01';
      formData.value.template_path = getCanonicalTemplateName(formData.value.template_type);
      formData.value.packed_qty = formData.value.packed_qty === 1 ? 190 : formData.value.packed_qty;
      formData.value.pkg_prefix = formData.value.pkg_prefix || 'VHK0010237';
      formData.value.mfr_pn = formData.value.mfr_pn || 'NYS5998';
      formData.value.revision = formData.value.revision || 'B';
      formData.value.target_weight = null;
      formData.value.min_weight = 12.300;
      formData.value.max_weight = 12.700;
      formData.value.weight_unit = 'kg';
    } else if (code === 'UI') {
      formData.value.packing_mode = 'item_scan';
      formData.value.template_type = 'standard';
      formData.value.template_path = getCanonicalTemplateName(formData.value.template_type);
      formData.value.start_part = formData.value.start_part || 'VN';
      formData.value.packed_qty = formData.value.packed_qty === 190 ? 10 : formData.value.packed_qty;
    }
  };

  const isErroProduct = computed(() => {
    const currentProps = 'value' in props ? props.value : props;
    const cust = currentProps.customers.find(c => c.id === formData.value.customer_id);
    const code = (cust?.code || '').toUpperCase();
    return code === 'ERRO' || ['erro_01', 'erro_02', 'erro_03', 'erro_04', 'erro_05'].includes(formData.value.template_type);
  });

  const onTemplateTypeChange = () => {
    if (formData.value.template_type === 'erro_05') {
      formData.value.template_path = 'erro_05.btw';
      formData.value.packing_mode = 'weight_scale';
      formData.value.pkg_prefix = formData.value.pkg_prefix || 'MC220TW1';
      formData.value.packed_qty = formData.value.packed_qty === 1 ? 1000 : formData.value.packed_qty;
      formData.value.min_weight = formData.value.min_weight ?? 0;
      formData.value.max_weight = formData.value.max_weight ?? 10;
      formData.value.target_weight = formData.value.target_weight ?? 5;
      formData.value.revision = formData.value.revision || '';
    } else if (formData.value.template_type === 'erro_04') {
      formData.value.template_path = 'erro_04.btw';
      formData.value.packing_mode = 'weight_scale';
      formData.value.min_weight = formData.value.min_weight ?? 0;
      formData.value.max_weight = formData.value.max_weight ?? 10;
      formData.value.target_weight = formData.value.target_weight ?? 5;
    } else if (formData.value.template_type === 'erro_03') {
      formData.value.template_path = 'erro_03.btw';
      formData.value.packing_mode = 'weight_scale';
      formData.value.pkg_prefix = formData.value.pkg_prefix || '1012665';
      formData.value.packed_qty = formData.value.packed_qty === 1 ? 190 : formData.value.packed_qty;
      formData.value.min_weight = formData.value.min_weight ?? 5.0;
      formData.value.max_weight = formData.value.max_weight ?? 7.0;
      formData.value.target_weight = formData.value.target_weight ?? 6.0;
      formData.value.revision = formData.value.revision || '/';
    } else if (formData.value.template_type === 'erro_02') {
      formData.value.template_path = 'erro_02.btw';
      formData.value.packing_mode = 'weight_scale';
      formData.value.pkg_prefix = formData.value.pkg_prefix || '37033907';
      formData.value.packed_qty = formData.value.packed_qty === 1 ? 190 : formData.value.packed_qty;
      formData.value.min_weight = formData.value.min_weight ?? 5.0;
      formData.value.max_weight = formData.value.max_weight ?? 7.0;
      formData.value.target_weight = formData.value.target_weight ?? 6.0;
    } else if (formData.value.template_type === 'erro_01') {
      formData.value.template_path = 'erro_01.btw';
      formData.value.packing_mode = 'weight_scale';
      formData.value.pkg_prefix = formData.value.pkg_prefix || 'VHK0010237';
      formData.value.packed_qty = formData.value.packed_qty === 1 ? 190 : formData.value.packed_qty;
      formData.value.min_weight = formData.value.min_weight ?? 12.300;
      formData.value.max_weight = formData.value.max_weight ?? 12.700;
    } else if (formData.value.template_type === 'detailed') {
      if (!formData.value.template_path || !formData.value.template_path.includes('detail')) {
        formData.value.template_path = 'carton_detail_1M_W.btw';
      }
    } else if (formData.value.template_type === 'standard') {
      if (!formData.value.template_path || formData.value.template_path.includes('detail')) {
        formData.value.template_path = 'carton_base.btw';
      }
    }
  };

  watch(
    () => {
      const p = 'value' in props ? props.value : props;
      return [p.show, p.initialData] as const;
    },
    ([isOpen]) => {
      if (!isOpen) return;
      const currentProps = 'value' in props ? props.value : props;
      loadTemplates();
      validationStatus.value = null;
      if (currentProps.isEdit && currentProps.initialData) {
        const p = currentProps.initialData;
        formData.value = {
          item_name: p.item_name,
          upc: p.upc || '',
          packed_qty: p.packed_qty,
          start_part: p.start_part || '',
          middle_part: p.middle_part || '',
          template_type: (p.template_type as any) || 'standard',
          template_path: getBaseName(p.template_path || ''),
          allow_partial: p.allow_partial || 0,
          customer_id: p.customer_id,
          packing_mode: p.packing_mode || 'item_scan',
          target_weight: p.target_weight ?? null,
          min_weight: p.min_weight ?? 12.300,
          max_weight: p.max_weight ?? 12.700,
          weight_unit: p.weight_unit || 'kg',
          mfr_pn: p.mfr_pn || 'NYS5998',
          pkg_prefix: p.pkg_prefix || 'VHK0010237',
          revision: p.revision ?? '',
          asin: p.asin || '',
          product_desc: p.product_desc || '',
          customer_project: p.customer_project || '',
          production_stage: p.production_stage || '',
          luxshare_part_number: p.luxshare_part_number || '',
          internal_factory_part_number: p.internal_factory_part_number || '',
          factory_item_code: p.factory_item_code || '',
          carton_id_prefix: p.carton_id_prefix || '',
        };
      } else {
        const defaultCustomerId = currentProps.customers.length > 0 ? currentProps.customers[0].id : null;
        formData.value = {
          item_name: '',
          upc: '',
          packed_qty: 1,
          start_part: 'VN',
          middle_part: '',
          template_type: 'standard',
          template_path: 'carton_base.btw',
          allow_partial: 0,
          customer_id: defaultCustomerId,
          packing_mode: 'item_scan',
          target_weight: null,
          min_weight: 12.300,
          max_weight: 12.700,
          weight_unit: 'kg',
          mfr_pn: 'NYS5998',
          pkg_prefix: 'VHK0010237',
          revision: 'B',
          asin: '',
          product_desc: '',
          customer_project: '',
          production_stage: '',
          luxshare_part_number: '',
          internal_factory_part_number: '',
          factory_item_code: '',
          carton_id_prefix: '',
        };
        if (defaultCustomerId) {
          onCustomerChange();
        }
      }
    },
    { immediate: true }
  );

  const setPackingMode = (mode: 'item_scan' | 'weight_scale') => {
    formData.value.packing_mode = mode;
    const isErro = ['erro_01', 'erro_02', 'erro_03', 'erro_04', 'erro_05'].includes(formData.value.template_type);
    if (mode === 'weight_scale' && !isErro) {
      formData.value.template_type = 'erro_01';
      formData.value.template_path = 'erro_01.btw';
    } else if (mode === 'item_scan' && isErro) {
      formData.value.template_type = 'standard';
      formData.value.template_path = 'carton_base.btw';
    }
  };

  const handleSubmit = () => {
    if (formData.value.packing_mode === 'weight_scale') {
      if (formData.value.min_weight === null || formData.value.min_weight === undefined ||
          formData.value.max_weight === null || formData.value.max_weight === undefined) {
        system.showNotification('Vui lòng nhập đầy đủ Min Weight và Max Weight', 'warning');
        return;
      }
      if (formData.value.min_weight > formData.value.max_weight) {
        system.showNotification('Trọng lượng Tối thiểu (Min) không được lớn hơn Tối đa (Max)', 'error');
        return;
      }
    }
    if (isErroProduct.value) {
      formData.value.template_path = getCanonicalTemplateName(formData.value.template_type);
    } else {
      formData.value.template_path = formData.value.template_path || (formData.value.template_type === 'detailed' ? 'carton_detail_1M_W.btw' : 'carton_base.btw');
    }
    emit('submit', { ...formData.value });
  };

  return {
    formData,
    availableTemplates,
    UI_TEMPLATES,
    isErroProduct,
    isValidating,
    validationStatus,
    formatBytes,
    getBaseName,
    getCanonicalTemplateName,
    checkTemplateValidity,
    setPackingMode,
    onCustomerChange,
    onTemplateTypeChange,
    handleSubmit,
  };
}
