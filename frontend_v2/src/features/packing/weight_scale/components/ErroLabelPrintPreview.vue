<template>
  <section class="rounded-xl border border-slate-200 bg-white shadow-xs flex-1 flex flex-col min-h-0 overflow-hidden">
    <header class="px-3.5 py-2.5 border-b border-slate-100 flex items-center justify-between shrink-0">
      <div class="flex items-center gap-1.5">
        <i class="fas fa-tags text-indigo-500"></i>
        <span class="font-bold text-xs text-slate-900">{{ t('erro.label_preview') }}</span>
      </div>
      <span class="text-[10px] font-black uppercase rounded bg-indigo-50 text-indigo-700 px-1.5 py-0.5">
        {{ product?.template_type || '-' }}
      </span>
    </header>

    <div v-if="errors.length" data-testid="preview-errors" class="mx-3.5 mt-3 rounded-lg border border-rose-200 bg-rose-50 p-2 text-xs text-rose-800">
      <p class="font-bold">{{ t('erro.cannot_print_missing', { fields: errors.join(', ') }) }}</p>
    </div>

    <div v-if="product?.template_type === 'erro_02'" class="p-3.5 space-y-2 text-xs overflow-y-auto">
      <PreviewField label="Product Name" :value="productName" />
      <div class="grid grid-cols-2 gap-2">
        <PreviewField label="QTY" :value="String(product.packed_qty)" />
        <PreviewField label="P/N" :value="product.mfr_pn" />
        <PreviewField label="ASIN" :value="product.asin" />
        <PreviewField label="Unit UPC" :value="product.upc" />
      </div>
      <PreviewField label="SSCC (00)" :value="ssccText" />
      <PreviewField label="Check Digit" :value="ssccCheckDigit" />
      <div class="h-10 rounded border border-dashed border-slate-300 bg-slate-50 flex items-center justify-center text-[10px] font-bold text-slate-400 uppercase tracking-widest">
        {{ t('erro.barcode_preview') }}
      </div>
    </div>

    <div v-else-if="product?.template_type === 'erro_04'" class="p-3.5 space-y-2 text-xs overflow-y-auto">
      <div class="grid grid-cols-2 gap-2">
        <PreviewField label="UPC" :value="product.upc" />
        <PreviewField label="SKU" :value="product.item_name" />
        <PreviewField label="Carton ID" :value="cartonSN" />
        <PreviewField label="Supplier P/N" :value="product.mfr_pn" />
        <PreviewField label="PO" :value="po" />
        <PreviewField label="Date" :value="dateYYMMDD" />
        <PreviewField label="QTY" :value="String(product.packed_qty)" />
        <PreviewField label="Rev" :value="product.revision" />
      </div>
      <PreviewField label="SKU Description" :value="product.product_desc" />
      <div class="h-10 rounded border border-dashed border-slate-300 bg-slate-50 flex items-center justify-center text-[10px] font-bold text-slate-400 uppercase tracking-widest">
        {{ t('erro.barcode_preview') }}
      </div>
    </div>

    <div v-else-if="product" class="p-3.5 space-y-2 text-xs overflow-y-auto">
      <div class="grid grid-cols-2 gap-2">
        <PreviewField v-for="field in fields" :key="field.label" :label="field.label" :value="field.value" />
      </div>
      <div class="h-10 rounded border border-dashed border-slate-300 bg-slate-50 flex items-center justify-center text-[10px] font-bold text-slate-400 uppercase tracking-widest">
        {{ t('erro.barcode_qr_preview') }}
      </div>
    </div>

    <div v-else class="p-4 text-center text-xs text-slate-400">
      {{ t('erro.choose_product_for_preview') }}
    </div>
  </section>
</template>

<script setup lang="ts">
import { computed, defineComponent, h, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Product } from '../../../../types/api';

const { t } = useI18n();

const props = defineProps<{
  product: Product | null;
  cartonSN: string;
  po: string;
  lot: string;
  now: Date;
}>();

const emit = defineEmits<{
  (event: 'validation-change', errors: string[]): void;
}>();

const PreviewField = defineComponent({
  props: { label: { type: String, required: true }, value: { type: String, default: '' } },
  setup(fieldProps) {
    return () => h('div', { class: 'rounded border border-slate-100 bg-slate-50 p-2' }, [
      h('p', { class: 'text-[10px] uppercase font-bold text-slate-400 mb-0.5' }, fieldProps.label),
      h('p', { class: 'font-mono font-semibold text-slate-800 break-words' }, fieldProps.value || '—'),
    ]);
  },
});

const productName = computed(() => {
  if (!props.product) return '';
  return props.product.product_desc ? `Product name:${props.product.product_desc}` : props.product.item_name;
});

const ssccText = computed(() => {
  const sn = ssccDigits.value;
  return sn.length >= 16 && sn.startsWith('0')
    ? `(00) 0 ${sn.slice(1, 9)} ${sn.slice(9, 16)}`
    : props.cartonSN;
});

const ssccDigits = computed(() => props.cartonSN.replace(/^\(00\)\s*/, '').replace(/\D/g, ''));

const ssccCheckDigit = computed(() => {
  const digits = ssccDigits.value;
  if (digits.length >= 17) return digits.slice(16, 17);
  if (digits.length !== 16) return '';
  const total = [...digits].reverse().reduce((sum, char, index) => sum + Number(char) * (index % 2 === 0 ? 3 : 1), 0);
  return String((10 - (total % 10)) % 10);
});

const dateYYMMDD = computed(() => {
  const year = String(props.now.getFullYear()).slice(-2);
  const month = String(props.now.getMonth() + 1).padStart(2, '0');
  const day = String(props.now.getDate()).padStart(2, '0');
  return `${year}${month}${day}`;
});

const lotNumber = computed(() => {
  const year = props.now.getFullYear();
  const month = String(props.now.getMonth() + 1).padStart(2, '0');
  const day = String(props.now.getDate()).padStart(2, '0');
  return props.lot || `${year}${month}${day}`;
});

const errors = computed(() => {
  if (!props.product) return [];
  const missing: string[] = [];
  const product = props.product;
  const need = (value: string | undefined, label: string) => {
    if (!value?.trim()) missing.push(label);
  };
  if (product.template_type === 'erro_01') {
    need(product.item_name, 'CPN'); need(product.mfr_pn, 'Mfr P/N'); need(props.po, 'PO Number'); need(lotNumber.value, 'Lot Number');
  } else if (product.template_type === 'erro_02') {
    need(product.product_desc, 'Product Name'); need(product.mfr_pn, 'P/N'); need(product.asin, 'ASIN'); need(product.upc, 'Unit UPC');
  } else if (product.template_type === 'erro_03') {
    need(product.customer_project, 'Customer Project'); need(product.production_stage, 'Production Stage'); need(product.luxshare_part_number, 'Luxshare Part No.'); need(product.product_desc, 'Part Description');
  } else if (product.template_type === 'erro_04') {
    need(product.upc, 'UPC'); need(props.po, 'PO Number'); need(product.revision, 'Revision'); need(product.product_desc, 'SKU Description');
  } else if (product.template_type === 'erro_05') {
    need(product.item_name, 'Item'); need(product.product_desc, 'Description');
  }
  return missing;
});

const dateYYYYMMDD = computed(() => `${props.now.getFullYear()}${String(props.now.getMonth() + 1).padStart(2, '0')}${String(props.now.getDate()).padStart(2, '0')}`);
const dateCode = computed(() => {
  const date = new Date(Date.UTC(props.now.getFullYear(), props.now.getMonth(), props.now.getDate()));
  const day = date.getUTCDay() || 7;
  date.setUTCDate(date.getUTCDate() + 4 - day);
  const start = new Date(Date.UTC(date.getUTCFullYear(), 0, 1));
  return `${String(props.now.getFullYear()).slice(-2)}${String(Math.ceil((((date.getTime() - start.getTime()) / 86400000) + 1) / 7)).padStart(2, '0')}`;
});
const fields = computed(() => {
  const product = props.product;
  if (!product) return [];
  if (product.template_type === 'erro_01') return [
    { label: 'CPN', value: product.item_name }, { label: 'QTY', value: String(product.packed_qty) }, { label: 'Mfr P/N', value: product.mfr_pn || '' }, { label: 'Date Code', value: dateCode.value }, { label: 'Lot No.', value: lotNumber.value }, { label: 'PO No.', value: props.po }, { label: 'Carton SN', value: props.cartonSN }, { label: 'Rev', value: product.revision || '' }, { label: 'Origin', value: 'MADE IN VIETNAM' },
  ];
  if (product.template_type === 'erro_03') return [
    { label: 'Project / Stage', value: `项目: ${product.customer_project || ''} | 生产阶段：${product.production_stage || ''}` }, { label: 'Luxshare Part No.', value: product.luxshare_part_number || '' }, { label: 'APN Rev', value: product.revision || '/' }, { label: 'QTY', value: String(product.packed_qty) }, { label: 'Date', value: dateYYYYMMDD.value }, { label: 'Lot No.', value: lotNumber.value }, { label: 'Part Description', value: product.product_desc || product.item_name }, { label: 'Supplier Code', value: product.pkg_prefix || '1012665' }, { label: 'Carton SN', value: props.cartonSN }, { label: 'Supplier Name', value: 'NIENYI VIETNAM INDUSTRIAL COMPANY LIMITED' }, { label: 'Origin', value: 'VIETNAM' },
  ];
  if (product.template_type === 'erro_05') return [
    { label: 'Carton No.', value: props.cartonSN }, { label: 'Item', value: product.item_name }, { label: 'Description', value: product.product_desc || '' }, { label: 'Date Code', value: dateCode.value }, { label: 'Lot Code', value: lotNumber.value }, { label: 'QTY', value: String(product.packed_qty) }, { label: 'MPN', value: '' }, { label: 'Rev', value: product.revision || '' }, { label: 'Config', value: '' }, { label: 'Batch', value: props.po }, { label: 'Stage', value: '' },
  ];
  return [];
});

watch(errors, value => emit('validation-change', value), { immediate: true });
</script>
