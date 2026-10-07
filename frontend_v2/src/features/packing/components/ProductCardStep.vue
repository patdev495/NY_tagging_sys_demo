<template>
  <div class="flex-1 flex flex-col justify-center items-center py-8 md:py-14 animate-in">
    <div class="w-full max-w-[620px] space-y-4">
      <!-- Breadcrumb / Job Order Bar -->
      <div class="flex justify-between items-center px-1">
        <span class="text-xs text-slate-600 font-bold uppercase tracking-wider">
          {{ t('packing.job_order', 'Work Order') }}: <strong class="font-barcode-mono text-slate-900 text-sm">{{ jobOrder }}</strong>
        </span>
        <button 
          @click="$emit('changeJobOrder')" 
          class="text-blue-600 hover:text-blue-800 border-none bg-transparent font-bold cursor-pointer text-xs flex items-center gap-1.5 hover:underline"
        >
          <i class="fas fa-arrow-rotate-left"></i> {{ t('packing.change_job_order', 'Đổi Work Order khác') }}
        </button>
      </div>

      <!-- Main Product Confirmation Card -->
      <div 
        @click="$emit('enterScanning')"
        class="group cursor-pointer bg-slate-900 text-white rounded-xl p-6 md:p-8 shadow-xl border border-slate-800 hover:border-slate-700 relative overflow-hidden transition-all"
      >
        <div class="flex justify-between items-start mb-4">
          <span class="bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-md px-2.5 py-1 text-xs font-bold uppercase tracking-wider">
            {{ t('packing.confirm_product') }}
          </span>
          <span class="text-xs font-mono text-slate-400">
            UPC: <strong class="text-white font-barcode-mono">{{ jobOrderDetails?.product.upc || 'N/A' }}</strong>
          </span>
        </div>

        <!-- Product Item Name -->
        <h3 class="text-xl md:text-2xl font-black leading-tight mb-6 tracking-wide text-white">
          {{ jobOrderDetails?.product.item_name }}
        </h3>

        <!-- Key Metrics 3-Column Grid -->
        <div class="grid grid-cols-3 gap-3 border-t border-slate-800 pt-5 text-center">
          <div class="bg-slate-800/60 rounded-lg p-3 border border-slate-700/60">
            <span class="text-slate-400 text-xs uppercase font-bold block mb-1">{{ t('packing.specification') }}</span>
            <span class="text-lg md:text-xl font-black text-white font-barcode-mono">
              {{ jobOrderDetails?.product.packed_qty }} <span class="text-xs font-normal text-slate-400">{{ t('packing.pcs_per_carton') }}</span>
            </span>
          </div>

          <div class="bg-slate-800/60 rounded-lg p-3 border border-slate-700/60">
            <span class="text-slate-400 text-xs uppercase font-bold block mb-1">{{ t('packing.total_qty') }}</span>
            <span class="text-lg md:text-xl font-black text-emerald-400 font-barcode-mono">
              {{ jobOrderDetails?.total_qty }} <span class="text-xs font-normal text-slate-400">{{ t('packing.items_unit') }}</span>
            </span>
          </div>

          <div class="bg-slate-800/60 rounded-lg p-3 border border-slate-700/60">
            <span class="text-slate-400 text-xs uppercase font-bold block mb-1">{{ t('packing.total_cartons') }}</span>
            <span class="text-lg md:text-xl font-black text-blue-400 font-barcode-mono">
              {{ jobOrderDetails?.total_cartons }} <span class="text-xs font-normal text-slate-400">{{ t('packing.cartons_unit', 'thùng') }}</span>
            </span>
          </div>
        </div>
      </div>

      <!-- Prominent Primary Call-to-Action Button -->
      <div class="pt-2">
        <button
          @click="$emit('enterScanning')"
          class="w-full h-14 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-base rounded-xl transition-all shadow-md flex items-center justify-center gap-2.5 cursor-pointer active:scale-98"
          :title="t('packing.enter_scanning_hint')"
        >
          <span>{{ t('packing.start_packing_and_scan') }}</span>
          <span class="text-xs font-barcode-mono font-black px-2 py-0.5 bg-black/25 rounded tracking-wider">ENTER ↵</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import type { JobOrderDetails } from '../../../types/api';

defineProps<{
  jobOrder: string;
  jobOrderDetails: JobOrderDetails | null;
}>();

const emit = defineEmits<{
  (e: 'changeJobOrder'): void;
  (e: 'enterScanning'): void;
}>();

const { t } = useI18n();

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter') {
    e.preventDefault();
    emit('enterScanning');
  }
};

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown);
});
</script>
