<template>
  <section class="my-1.5 px-4 py-2 rounded-xl bg-slate-50/90 border border-slate-200/90 shadow-xs flex items-center justify-between gap-3 shrink-0">
    <div class="flex items-center gap-4 md:gap-6 flex-wrap">
      <!-- Job Order & Factory P/N -->
      <div v-if="activeJobOrder" class="flex items-center gap-2">
        <span class="text-xs uppercase tracking-wider font-bold text-slate-400">{{ t('erro.job_order_label') }}</span>
        <span class="font-black text-base md:text-lg text-indigo-900 font-mono">
          {{ activeJobOrder }}
        </span>
        <span class="font-mono text-xs font-bold text-slate-500">
          ({{ activeFactoryPartNumber }})
        </span>
      </div>

      <!-- CPN -->
      <div v-if="selectedProduct" class="flex items-center gap-2 border-l border-slate-200 pl-4 font-mono">
        <span class="text-xs uppercase tracking-wider font-bold text-slate-400 font-sans">CPN:</span>
        <span class="font-black text-base md:text-lg text-slate-900">
          {{ selectedProduct.item_name }}
        </span>
        <span class="px-2 py-0.5 rounded bg-indigo-100 text-indigo-700 font-bold text-xs">
          {{ selectedProduct.packed_qty }} PCS
        </span>
      </div>

      <!-- Progress (Clickable) -->
      <div v-if="selectedProduct && jobOrderPlannedCartons > 0" class="flex items-center gap-2 border-l border-slate-200 pl-4 font-mono">
        <span class="text-xs uppercase font-bold text-slate-400 font-sans">{{ t('erro.progress') }}</span>
        <button 
          type="button"
          @click="$emit('showCartons')"
          :title="t('erro.view_packed_cartons')"
          :class="['px-2.5 py-0.5 rounded-lg font-bold text-xs flex items-center gap-1.5 cursor-pointer hover:opacity-90 hover:scale-[1.02] active:scale-[0.98] transition-all', jobOrderPackedCartonsCount >= jobOrderPlannedCartons ? 'bg-amber-100 text-amber-900 border border-amber-300' : 'bg-emerald-50 text-emerald-800 border border-emerald-200']"
        >
          <span>{{ t('erro.carton_progress', { packed: jobOrderPackedCartonsCount, planned: jobOrderPlannedCartons }) }}</span>
          <span class="text-slate-400">({{ (jobOrderPackedCartonsCount * selectedProduct.packed_qty).toLocaleString() }} / {{ jobOrderTotalQty.toLocaleString() }} PCS)</span>
          <i class="fas fa-list-check text-indigo-600 text-[11px] ml-0.5"></i>
          <span v-if="jobOrderPackedCartonsCount >= jobOrderPlannedCartons" class="text-[10px] font-black text-amber-700 uppercase ml-0.5">⚠️ {{ t('erro.over_plan') }}</span>
        </button>
      </div>

      <!-- PO & LOT -->
      <div class="flex items-center gap-2 border-l border-slate-200 pl-4 font-mono">
        <span class="text-xs uppercase font-bold text-slate-400 font-sans">PO/LOT:</span>
        <span v-if="selectedProduct?.template_type === 'erro_02'" class="font-bold text-xs text-slate-500 italic bg-slate-100 px-2 py-0.5 rounded border border-slate-200">{{ t('erro.not_applicable_template_2') }}</span>
        <span v-else class="font-bold text-sm text-indigo-900">
          PO: {{ activePO || (['erro_03', 'erro_05'].includes(selectedProduct?.template_type || '') ? `(${t('common.optional')})` : t('erro.not_entered')) }}
          <span class="text-slate-300 mx-1">|</span>
          LOT: {{ activeLot || automaticLot() }}
        </span>
      </div>
    </div>

    <div class="flex items-center gap-2 shrink-0">
      <button 
        type="button"
        @click="$emit('openTemplate')"
        :disabled="isOpeningTemplate || !selectedProduct"
        class="px-2.5 py-1 rounded-lg bg-indigo-50 hover:bg-indigo-100 disabled:bg-slate-100 disabled:text-slate-400 border border-indigo-200 text-indigo-700 text-xs font-bold transition-all flex items-center gap-1.5 shadow-2xs hover:border-indigo-300 cursor-pointer disabled:cursor-not-allowed"
        :title="t('packing.open_template_tooltip')"
      >
        <i v-if="isOpeningTemplate" class="fas fa-spinner fa-spin text-indigo-600 text-xs"></i>
        <i v-else class="fas fa-file-lines text-indigo-600 text-xs"></i>
        <span>{{ t('packing.open_template_btn') }}</span>
      </button>
      <button 
        v-if="selectedProduct?.template_type !== 'erro_02'"
        @click="$emit('editBatch')" 
        class="px-2.5 py-1 rounded-lg bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 text-xs font-bold transition-all flex items-center gap-1 shadow-xs cursor-pointer"
      >
        <i class="fas fa-edit text-indigo-500"></i>
        <span>{{ t('erro.change_po_lot') }}</span>
      </button>
      <button @click="$emit('changeJobOrder')" :disabled="!selectedProduct" class="px-2.5 py-1 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white text-xs font-bold transition-all flex items-center gap-1 shadow-xs shadow-indigo-600/20 cursor-pointer">
        <i class="fas fa-boxes"></i>
        <span>{{ t('erro.change_job_order') }}</span>
      </button>
    </div>
  </section>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import type { Product } from '../../../../types/api';

const { t } = useI18n();

const automaticLot = () => {
  const now = new Date();
  return `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`;
};

defineProps<{
  activeJobOrder: string;
  activeFactoryPartNumber: string;
  selectedProduct: Product | null;
  jobOrderPlannedCartons: number;
  jobOrderPackedCartonsCount: number;
  jobOrderTotalQty: number;
  activePO: string;
  activeLot: string;
  isOpeningTemplate: boolean;
}>();

defineEmits<{
  (e: 'showCartons'): void;
  (e: 'openTemplate'): void;
  (e: 'editBatch'): void;
  (e: 'changeJobOrder'): void;
}>();
</script>
