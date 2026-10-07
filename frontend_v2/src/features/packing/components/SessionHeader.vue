<template>
  <div class="flex flex-col gap-2.5 mb-3 px-4 py-3 bg-white rounded-xl border border-slate-200 shadow-xs">
    <!-- Top Row: Product Title & Quick Specs -->
    <div class="flex items-center justify-between gap-3 w-full pb-2.5 border-b border-slate-200">
      <div class="flex items-center gap-3 min-w-0">
        <button 
          @click="$emit('back')" 
          class="w-9 h-9 flex items-center justify-center bg-slate-50 border border-slate-200 text-slate-600 rounded-lg cursor-pointer transition-all hover:bg-slate-100 hover:text-blue-600 hover:border-blue-300 shrink-0" 
          :title="t('packing.back')"
        >
          <i class="fas fa-arrow-left text-sm"></i>
        </button>
        <div class="min-w-0">
          <h2 class="m-0 text-base md:text-lg font-black text-slate-900 tracking-tight truncate" :title="product.item_name">
            {{ product.item_name }}
          </h2>
          <div class="flex items-center gap-2 mt-0.5 text-xs font-semibold text-slate-500">
            <span class="inline-flex items-center px-2 py-0.5 border border-slate-200 rounded bg-slate-50 font-barcode-mono text-slate-700">
              UPC: {{ product.upc }}
            </span>
            <span class="inline-flex items-center px-2 py-0.5 border border-emerald-200 rounded bg-emerald-50 text-emerald-800 font-bold">
              {{ t('packing.specification') }}: {{ product.packed_qty }} {{ t('packing.pcs_per_carton') }}
            </span>
          </div>
        </div>
      </div>

      <!-- Open Template Button -->
      <div class="flex items-center gap-2 shrink-0">
        <button
          type="button"
          @click="$emit('open-template')"
          :disabled="isOpeningTemplate"
          class="px-3 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border border-indigo-200 text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer shadow-2xs hover:border-indigo-300 disabled:opacity-50"
          :title="t('packing.open_template_tooltip', 'Mở file mẫu tem BarTender (.btw) trên máy trạm')"
        >
          <i v-if="isOpeningTemplate" class="fas fa-spinner fa-spin text-indigo-600 text-xs"></i>
          <i v-else class="fas fa-file-lines text-indigo-600 text-xs"></i>
          <span>{{ t('packing.open_template_btn', 'Mở Mẫu Tem') }}</span>
        </button>
      </div>
    </div>
    
    <!-- Bottom Row: Operational Inputs -->
    <div class="flex flex-wrap gap-2.5 items-end w-full">
      <!-- Công Lệnh (Readonly) -->
      <div class="flex flex-col gap-1 flex-1 min-w-[130px] max-w-[180px]">
        <label class="text-xs text-slate-600 font-bold uppercase tracking-wider pl-0.5">
          {{ t('packing.job_order') }}
        </label>
        <div class="w-full h-10 px-3 bg-slate-100 border border-slate-300 rounded-lg text-sm font-barcode-mono font-bold text-slate-800 flex items-center select-all">
          {{ jobOrder }}
        </div>
      </div>

      <!-- Xuất Xứ (Origin) -->
      <div class="flex flex-col gap-1 flex-none w-20">
        <label class="text-xs text-slate-600 font-bold uppercase tracking-wider pl-0.5">
          {{ t('packing.origin') }}
        </label>
        <select 
          :value="cartonOrigin"
          @change="onOriginChange"
          class="w-full h-10 px-2.5 bg-white border border-slate-300 rounded-lg text-sm font-bold text-slate-900 outline-none transition-colors focus:border-blue-600 focus:ring-2 focus:ring-blue-500/10 cursor-pointer"
        >
          <option value="VN">VN</option>
          <option value="CN">CN</option>
        </select>
      </div>

      <!-- Chọn Số Thùng (Carton Number) -->
      <div class="flex flex-col gap-1 flex-1 min-w-[180px] max-w-[260px]">
        <div class="flex justify-between items-center pl-0.5">
          <label class="text-xs text-slate-700 font-bold uppercase tracking-wider">
            {{ t('packing.carton_seq') }} ({{ cartonNumberRange || '...' }})
          </label>
          <span v-if="snPreview" class="text-[11px] font-bold text-emerald-700">
            {{ t('packing.ready') }}
          </span>
        </div>
        <div class="relative flex items-center">
          <input 
            :value="cartonNumberStr"
            @input="onCartonNumberInput"
            @keydown.enter.prevent="onCartonNumberSubmit"
            type="text"
            inputmode="numeric"
            :placeholder="t('packing.carton_num_example')" 
            class="w-full h-10 px-3 bg-white border rounded-lg text-sm font-barcode-mono font-bold outline-none transition-all shadow-2xs"
            :class="hasCartonNumberError 
              ? 'border-rose-500 text-rose-700 focus:border-rose-500 focus:ring-2 focus:ring-rose-500/15 bg-rose-50/40' 
              : 'border-slate-300 text-slate-900 focus:border-blue-600 focus:ring-2 focus:ring-blue-500/10'"
            ref="cartonInput"
          />
        </div>
        <!-- Error hint -->
        <div 
          v-if="hasCartonNumberError && cartonNumberErrorText"
          class="text-xs text-rose-700 bg-rose-50 px-2 py-1 rounded border border-rose-200 font-bold flex items-center gap-1 mt-0.5"
        >
          <i class="fas fa-exclamation-circle text-rose-600"></i>
          <span>{{ cartonNumberErrorText }}</span>
        </div>
        <!-- SN Preview badge -->
        <div 
          v-else-if="snPreview"
          class="text-xs text-slate-700 mt-0.5 bg-slate-50 px-2 py-0.5 rounded border border-slate-200 flex items-center justify-between"
        >
          <span class="text-slate-500 text-[11px]">{{ t('packing.carton_sn_label') }}</span>
          <strong class="font-barcode-mono text-emerald-700 font-extrabold text-[12px]">{{ snPreview }}</strong>
        </div>
      </div>

      <!-- Tiền tố quét (Pattern) -->
      <div class="flex flex-col gap-1 flex-none w-[90px]">
        <label class="text-xs text-slate-600 font-bold uppercase tracking-wider pl-0.5">
          {{ t('packing.sn_pattern') }}
        </label>
        <input 
          :value="snPattern"
          @input="onPatternInput"
          :placeholder="t('packing.pattern_placeholder')" 
          class="w-full h-10 px-2.5 bg-white rounded-lg text-sm font-barcode-mono font-bold outline-none transition-colors border border-slate-300 text-slate-800 focus:border-blue-600 focus:ring-2 focus:ring-blue-500/10"
          @keyup.enter="$emit('focus-scan')"
        />
      </div>

      <!-- Tháng/Năm tem (YYMM) -->
      <div class="flex flex-col gap-1 flex-none w-[80px]">
        <label class="text-xs text-slate-600 font-bold uppercase tracking-wider pl-0.5">
          {{ t('packing.manual_date') }}
        </label>
        <div class="w-full h-10 px-2 bg-slate-100 border border-slate-300 rounded-lg text-xs font-barcode-mono font-bold text-slate-600 flex items-center justify-center select-none">
          {{ customYYMM || '-' }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Product } from '../../../types/api';

const props = defineProps<{
  product: Product;
  jobOrder: string;
  cartonOrigin: string;
  cartonNumberStr: string;
  cartonNumberRange?: string;
  snPreview?: string;
  snPattern?: string;
  customYYMM?: string;
  hasCartonNumberError?: boolean;
  cartonNumberErrorText?: string;
  isOpeningTemplate?: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:cartonOrigin', val: string): void;
  (e: 'update:cartonNumberStr', val: string): void;
  (e: 'update:snPattern', val: string): void;
  (e: 'back'): void;
  (e: 'focus-scan'): void;
  (e: 'submit-carton-number'): void;
  (e: 'clear-carton-error'): void;
  (e: 'open-template'): void;
}>();

const { t } = useI18n();
const cartonInput = ref<HTMLInputElement | null>(null);

const onOriginChange = (e: Event) => {
  emit('update:cartonOrigin', (e.target as HTMLSelectElement).value);
};

const onCartonNumberInput = (e: Event) => {
  emit('clear-carton-error');
  emit('update:cartonNumberStr', (e.target as HTMLInputElement).value);
};

const onCartonNumberSubmit = () => {
  emit('submit-carton-number');
};

const onPatternInput = (e: Event) => {
  emit('update:snPattern', (e.target as HTMLInputElement).value);
};

const focusCartonInput = () => {
  if (cartonInput.value) {
    cartonInput.value.focus();
    cartonInput.value.select();
  }
};

defineExpose({
  focusCartonInput,
});
</script>
