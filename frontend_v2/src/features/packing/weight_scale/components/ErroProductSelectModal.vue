<template>
  <div 
    v-if="show" 
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/70 select-none animate-in"
    role="dialog"
    aria-modal="true"
  >
    <div class="bg-white rounded-xl shadow-2xl max-w-lg w-full p-5 border border-slate-300 flex flex-col gap-4">
      <!-- Modal Header -->
      <div class="flex items-center justify-between pb-3 border-b border-slate-200">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-lg bg-emerald-100 text-emerald-800 flex items-center justify-center font-bold">
            <i class="fas fa-boxes text-sm"></i>
          </div>
          <div>
            <h2 class="font-bold text-base text-slate-900 leading-tight">Chọn Sản Phẩm Khách Hàng Erro</h2>
            <p class="text-xs text-slate-500 m-0">Chọn mã sản phẩm để thiết lập dải trọng lượng cân</p>
          </div>
        </div>
        <div class="flex items-center gap-1.5">
          <button 
            @click="$emit('reload')" 
            :disabled="isLoading" 
            class="w-8 h-8 rounded-lg border border-slate-300 text-slate-600 hover:text-emerald-700 hover:bg-slate-50 flex items-center justify-center transition-colors cursor-pointer disabled:opacity-50"
            title="Làm mới danh sách sản phẩm từ CSDL"
          >
            <i :class="['fas fa-rotate text-xs', isLoading ? 'animate-spin text-emerald-600' : '']"></i>
          </button>
          <button 
            @click="$emit('close')" 
            class="w-8 h-8 rounded-lg border border-slate-300 text-slate-600 hover:text-slate-900 hover:bg-slate-50 flex items-center justify-center transition-colors cursor-pointer"
            title="Đóng (Esc)"
          >
            <i class="fas fa-times text-xs"></i>
          </button>
        </div>
      </div>

      <!-- Products List or States -->
      <div class="space-y-2 max-h-[60vh] overflow-y-auto">
        <!-- Loading State -->
        <div v-if="isLoading" class="py-10 flex flex-col items-center justify-center text-slate-500 gap-2">
          <i class="fas fa-spinner fa-spin text-2xl text-emerald-600"></i>
          <span class="text-xs font-semibold">Đang tải danh sách sản phẩm Erro từ CSDL...</span>
        </div>

        <!-- Empty State -->
        <div v-else-if="!products || products.length === 0" class="py-8 px-4 text-center bg-slate-50 rounded-xl border border-slate-200">
          <div class="w-12 h-12 rounded-full bg-slate-100 border border-slate-200 text-slate-400 flex items-center justify-center mx-auto mb-2">
            <i class="fas fa-box-open text-lg"></i>
          </div>
          <h4 class="font-bold text-sm text-slate-800 mb-1">Chưa có sản phẩm Erro nào</h4>
          <p class="text-xs text-slate-500 max-w-xs mx-auto leading-relaxed mb-3">
            Hệ thống chưa tìm thấy sản phẩm nào được gán cho Khách hàng Erro trong cơ sở dữ liệu.
          </p>
          <button 
            @click="$emit('reload')"
            class="px-3 py-1.5 bg-white border border-slate-300 rounded-lg text-xs font-bold text-slate-700 hover:bg-slate-50 cursor-pointer inline-flex items-center gap-1.5"
          >
            <i class="fas fa-rotate text-[10px]"></i>
            <span>Tải Lại CSDL</span>
          </button>
        </div>

        <!-- Products grouped by label format -->
        <div v-else class="space-y-4">
          <div class="flex flex-wrap gap-2" aria-label="Lọc theo mẫu tem">
            <button
              v-for="filter in templateFilters"
              :key="filter.key"
              type="button"
              @click="selectedTemplate = filter.key"
              :aria-pressed="selectedTemplate === filter.key"
              :class="[
                'px-2.5 py-1.5 rounded-lg border text-xs font-bold transition-colors cursor-pointer',
                selectedTemplate === filter.key
                  ? 'border-emerald-600 bg-emerald-600 text-white'
                  : 'border-slate-200 bg-white text-slate-600 hover:border-emerald-300 hover:text-emerald-700'
              ]"
            >
              {{ filter.label }} <span class="opacity-75">({{ filter.count }})</span>
            </button>
          </div>

          <section v-for="group in visibleTemplateGroups" :key="group.key" class="space-y-2">
            <div class="flex items-center gap-2">
              <span :class="['w-2 h-2 rounded-full', group.dotClass]"></span>
              <h3 class="text-xs font-black uppercase tracking-wide text-slate-700">{{ group.label }}</h3>
              <span class="text-[11px] text-slate-400">{{ group.products.length }} sản phẩm</span>
            </div>

            <button
              v-for="p in group.products"
              :key="p.id"
              type="button"
              @click="$emit('select', p)"
              :aria-pressed="selectedProduct?.id === p.id"
              :class="[
                'w-full text-left p-3.5 rounded-xl border transition-all cursor-pointer flex items-center justify-between',
                selectedProduct?.id === p.id
                  ? 'border-emerald-600 bg-emerald-50/70 shadow-xs'
                  : 'border-slate-200 hover:border-emerald-300 hover:bg-slate-50'
              ]"
            >
              <div>
                <div class="flex items-center gap-2">
                  <h4 class="font-black text-sm md:text-base text-slate-900 font-barcode-mono">{{ p.item_name }}</h4>
                  <span class="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-xs font-bold">{{ p.packed_qty }} PCS</span>
                </div>
                <p class="text-xs text-slate-500 mt-1 mb-0.5">
                  Mfr P/N: <strong class="text-slate-700 font-barcode-mono">{{ p.mfr_pn || 'NYS5998' }}</strong> |
                  Tiền tố: <strong class="text-slate-700 font-barcode-mono">{{ p.template_type === 'erro_04' ? (p.carton_id_prefix || '-') : (p.pkg_prefix || 'VHK0010237') }}</strong>
                </p>
                <p class="text-xs text-emerald-700 font-barcode-mono font-bold mt-0.5 mb-0">
                  Dung sai cân: {{ p.min_weight?.toFixed(3) || '0.000' }}kg - {{ p.max_weight?.toFixed(3) || '0.000' }}kg
                </p>
              </div>
              <div v-if="selectedProduct?.id === p.id" class="w-6 h-6 rounded-full bg-emerald-600 text-white flex items-center justify-center text-xs shrink-0">
                <i class="fas fa-check"></i>
              </div>
            </button>
          </section>
        </div>
      </div>

      <!-- Footer -->
      <div class="flex justify-end pt-2 border-t border-slate-200">
        <button
          @click="$emit('close')"
          class="px-4 py-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition-colors cursor-pointer"
        >
          Đóng
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Product } from '../../../../types/api';

const { t } = useI18n();

const props = defineProps<{
  show: boolean;
  products: Product[];
  selectedProduct: Product | null;
  isLoading?: boolean;
}>();

const selectedTemplate = ref('all');

const templateGroups = computed(() => {
  const definitions = [
    { key: 'erro_01', label: 'Erro 01 · Carton SN', dotClass: 'bg-emerald-500' },
    { key: 'erro_02', label: 'Erro 02 · SSCC', dotClass: 'bg-sky-500' },
    { key: 'erro_03', label: 'Erro 03 · Luxshare', dotClass: 'bg-amber-500' },
    { key: 'erro_04', label: 'Erro 04 · PD027032', dotClass: 'bg-rose-500' },
    { key: 'erro_05', label: 'Erro 05 · Pegatron NN9', dotClass: 'bg-teal-500' },
  ];

  const groups = definitions.map(definition => ({
    ...definition,
    products: props.products.filter(product => product.template_type === definition.key),
  })).filter(group => group.products.length > 0);

  const otherProducts = props.products.filter(product => !definitions.some(definition => definition.key === product.template_type));
  if (otherProducts.length > 0) {
    groups.push({ key: 'other', label: 'Khác', dotClass: 'bg-slate-400', products: otherProducts });
  }
  return groups;
});

const templateFilters = computed(() => [
  { key: 'all', label: 'Tất cả', count: props.products.length },
  ...templateGroups.value.map(group => ({ key: group.key, label: group.label.split(' · ')[0], count: group.products.length })),
]);

const visibleTemplateGroups = computed(() => (
  selectedTemplate.value === 'all'
    ? templateGroups.value
    : templateGroups.value.filter(group => group.key === selectedTemplate.value)
));

defineEmits<{
  (e: 'close'): void;
  (e: 'select', product: Product): void;
  (e: 'reload'): void;
}>();
</script>
