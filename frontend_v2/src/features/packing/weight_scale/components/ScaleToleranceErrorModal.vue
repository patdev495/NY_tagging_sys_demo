<template>
  <div 
    v-if="show" 
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in"
    @click.self="$emit('close')"
  >
    <div class="bg-white rounded-3xl shadow-2xl max-w-lg w-full p-6 md:p-7 border-2 border-rose-500 flex flex-col gap-4 md:gap-5 relative overflow-hidden animate-shake">
      <!-- Top Accent Gradient Line -->
      <div class="absolute top-0 left-0 right-0 h-2 bg-gradient-to-r from-rose-500 via-amber-500 to-rose-500"></div>

      <!-- Modal Header -->
      <div class="flex items-center gap-3.5">
        <div class="w-13 h-13 md:w-14 md:h-14 rounded-2xl bg-rose-100 border border-rose-200 flex items-center justify-center text-rose-600 text-2xl shrink-0 shadow-inner">
          <i class="fas fa-triangle-exclamation animate-bounce"></i>
        </div>
        <div>
          <span class="px-2 py-0.5 rounded-md bg-rose-100 text-rose-800 font-extrabold text-[10px] uppercase tracking-wider">
            {{ t('erro.weight_print_locked') }}
          </span>
          <h2 class="font-black text-lg md:text-xl text-slate-900 leading-tight mt-0.5">
            {{ details?.title || t('erro.invalid_weight') }}
          </h2>
        </div>
      </div>

      <!-- Alert Message Detail Box -->
      <div class="p-3 rounded-xl bg-rose-50 border border-rose-200/80 text-rose-900 text-xs md:text-sm font-semibold flex items-center gap-2.5">
        <i class="fas fa-circle-exclamation text-rose-600 text-base shrink-0"></i>
        <span>{{ details?.message || t('erro.weight_outside_range') }}</span>
      </div>

      <!-- Weight Comparison Cards Grid -->
      <div class="grid grid-cols-2 gap-2.5">
        <!-- Current Measured Weight -->
        <div class="p-3.5 rounded-2xl bg-slate-900 text-white flex flex-col justify-between shadow-md">
          <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">{{ t('erro.measured_weight') }}</span>
          <div class="my-1">
            <span class="text-3xl md:text-4xl font-black font-mono text-rose-400">
              {{ formatWeight(details?.currentWeight) }}
            </span>
            <span class="text-xs font-bold text-slate-400 font-mono ml-1">kg</span>
          </div>
          <span class="text-[10px] font-bold text-rose-300 flex items-center gap-1">
            <i class="fas fa-times-circle"></i> {{ t('erro.outside_range') }}
          </span>
        </div>

        <!-- Standard Product Target Range -->
        <div class="p-3.5 rounded-2xl bg-slate-50 border border-slate-200 flex flex-col justify-between">
          <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500">{{ t('erro.allowed_range') }}</span>
          <div class="space-y-1.5 my-1 text-xs">
            <div class="flex justify-between font-mono">
              <span class="text-slate-500">{{ t('erro.minimum') }}</span>
              <strong class="text-slate-800">{{ formatWeight(details?.minWeight) }} kg</strong>
            </div>
            <div class="flex justify-between font-mono">
              <span class="text-slate-500">{{ t('erro.maximum') }}</span>
              <strong class="text-slate-800">{{ formatWeight(details?.maxWeight) }} kg</strong>
            </div>
          </div>
          <span class="text-[10px] font-bold text-emerald-700 flex items-center gap-1">
            <i class="fas fa-check-circle"></i> {{ t('erro.product_standard') }}
          </span>
        </div>
      </div>

      <!-- Operator Action Guide -->
      <div class="text-xs text-slate-600 leading-relaxed bg-slate-50 p-2.5 rounded-xl border border-slate-200">
        👉 <strong>{{ t('erro.guide') }}</strong> {{ t('erro.weight_tolerance_guide') }}
      </div>

      <!-- Confirm / Dismiss Action Button -->
      <button
        @click="$emit('close')"
        class="w-full py-3.5 rounded-xl bg-rose-600 hover:bg-rose-700 active:scale-[0.99] text-white font-black text-sm md:text-base transition-all flex items-center justify-center gap-2 cursor-pointer shadow-lg shadow-rose-600/30"
      >
        <i class="fas fa-check text-base"></i>
        <span>{{ t('erro.acknowledge') }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

defineProps<{
  show: boolean;
  details: {
    status?: string;
    title?: string;
    message?: string;
    currentWeight?: number;
    minWeight?: number;
    maxWeight?: number;
  } | null;
}>();

defineEmits<{
  (e: 'close'): void;
}>();

const formatWeight = (val?: number) => {
  if (val === undefined || val === null) return '0.000';
  return val.toFixed(3);
};
</script>
