<template>
  <div class="p-4 md:p-5 rounded-2xl bg-slate-900 text-white shadow-lg flex-1 flex flex-col justify-between relative overflow-hidden min-h-0">
    <!-- Background Glow Effect -->
    <div 
      :class="[
        'absolute -right-20 -top-20 w-72 h-72 rounded-full blur-3xl opacity-20 transition-all duration-500 pointer-events-none',
        (!isAgentOnline || !scaleStatus.connected) ? 'bg-slate-700' :
        toleranceResult.status === 'READY' ? 'bg-emerald-400' :
        toleranceResult.status === 'UNSTABLE' ? 'bg-amber-400' :
        toleranceResult.status === 'UNDERWEIGHT' || toleranceResult.status === 'OVERWEIGHT' ? 'bg-rose-500' : 'bg-slate-600'
      ]"
    ></div>

    <!-- Top Row: Scale Pulse & Status -->
    <div class="flex items-center justify-between mb-1 z-10 shrink-0">
      <div class="flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider">
        <i 
          :class="[
            'fas fa-satellite-dish',
            (isAgentOnline && scaleStatus.connected) ? 'text-emerald-400 animate-pulse' : 'text-slate-500'
          ]"
        ></i>
        <span class="text-slate-400">
          {{ (isAgentOnline && scaleStatus.connected) ? t('erro.live_scale_signal') : (!isAgentOnline ? t('erro.agent_disconnected') : t('erro.scale_port_disconnected')) }}
        </span>
      </div>
    </div>

    <!-- Big Digital Reading Display -->
    <div class="flex flex-col items-center justify-center my-auto py-1 z-10">
      <div class="flex items-baseline gap-2">
        <span 
          :class="[
            'text-6xl md:text-7xl lg:text-8xl font-black font-mono tracking-tight transition-colors duration-200 leading-none',
            (!isAgentOnline || !scaleStatus.connected) ? 'text-slate-600' :
            toleranceResult.status === 'READY' ? 'text-emerald-400' :
            toleranceResult.status === 'UNSTABLE' ? 'text-amber-400' :
            toleranceResult.status === 'UNDERWEIGHT' || toleranceResult.status === 'OVERWEIGHT' ? 'text-rose-400' : 'text-slate-500'
          ]"
        >
          {{ (!isAgentOnline || !scaleStatus.connected) ? '--.---' : formatWeight(scaleReading.weight) }}
        </span>
        <span class="text-xl md:text-2xl font-bold text-slate-400 font-mono">{{ scaleReading.unit || 'kg' }}</span>
      </div>

      <!-- Indicators: Stability & Tare -->
      <div class="flex items-center gap-2 mt-2">
        <span 
          :class="[
            'px-2.5 py-0.5 rounded-full text-[11px] font-bold flex items-center gap-1',
            !isAgentOnline
              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
              : (!scaleStatus.connected
                ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
                : (scaleReading.is_stable
                  ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                  : 'bg-amber-500/20 text-amber-300 border border-amber-500/30 animate-pulse'))
          ]"
        >
          <i 
            :class="[
              !isAgentOnline 
                ? 'fas fa-power-off' 
                : (!scaleStatus.connected 
                  ? 'fas fa-plug-circle-xmark' 
                  : (scaleReading.is_stable ? 'fas fa-check-circle' : 'fas fa-spinner fa-spin'))
            ]"
          ></i>
          <span>
            {{ 
              !isAgentOnline 
                ? t('erro.agent_offline') 
                : (!scaleStatus.connected 
                  ? t('erro.scale_not_connected') 
                  : (scaleReading.is_stable ? t('erro.stable') : t('erro.unstable'))) 
            }}
          </span>
        </span>

        <span v-if="isAgentOnline && scaleStatus.connected && scaleReading.is_tare" class="px-2 py-0.5 rounded-full text-[11px] font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
          {{ t('erro.tare_applied') }}
        </span>
      </div>
    </div>

    <!-- Visual Tolerance Bar & Targets -->
    <div class="pt-2.5 border-t border-slate-800/90 z-10 shrink-0">
      <!-- Prominent 2-Pillar Weight Badges (Min & Max) -->
      <div class="grid grid-cols-2 gap-3 mb-2">
        <!-- Min Limit Badge -->
        <div class="px-3 py-2 rounded-xl bg-slate-800/90 border border-amber-500/30 flex items-center justify-between shadow-xs">
          <div class="flex items-center gap-1.5 text-[11px] font-extrabold uppercase tracking-wider text-amber-400">
            <i class="fas fa-arrow-down-short-wide text-[10px]"></i>
            <span>{{ t('erro.minimum_label') }}</span>
          </div>
          <span class="font-mono font-black text-sm md:text-base text-slate-100">
            {{ selectedProduct?.min_weight?.toFixed(3) || '0.150' }} <span class="text-[11px] font-normal text-slate-400">kg</span>
          </span>
        </div>

        <!-- Max Limit Badge -->
        <div class="px-3 py-2 rounded-xl bg-slate-800/90 border border-rose-500/30 flex items-center justify-between shadow-xs">
          <div class="flex items-center gap-1.5 text-[11px] font-extrabold uppercase tracking-wider text-rose-400">
            <i class="fas fa-arrow-up-wide-short text-[10px]"></i>
            <span>{{ t('erro.maximum_label') }}</span>
          </div>
          <span class="font-mono font-black text-sm md:text-base text-slate-100">
            {{ selectedProduct?.max_weight?.toFixed(3) || '0.200' }} <span class="text-[11px] font-normal text-slate-400">kg</span>
          </span>
        </div>
      </div>

      <!-- High-Visibility Dynamic Gauge Track Bar -->
      <div class="relative h-4 bg-slate-950 rounded-full overflow-hidden p-0.5 flex items-center border border-slate-700 shadow-inner">
        <!-- Underweight Left Zone -->
        <div class="absolute left-0 w-[16.6%] h-full bg-amber-500/15"></div>
        <!-- Acceptable Green Safe Zone -->
        <div class="absolute left-[16.6%] right-[16.6%] h-full bg-gradient-to-r from-emerald-500/30 via-emerald-400/50 to-emerald-500/30 border-x border-emerald-400/60"></div>
        <!-- Overweight Right Zone -->
        <div class="absolute right-0 w-[16.6%] h-full bg-rose-500/15"></div>

        <!-- Dynamic Live Needle Pointer -->
        <div 
          :class="[
            'absolute top-0 bottom-0 w-3 -ml-1.5 rounded-full border shadow-md transition-all duration-150',
            toleranceResult.status === 'READY' ? 'bg-emerald-400 border-white shadow-[0_0_8px_rgba(52,211,153,1)]' :
            toleranceResult.status === 'UNSTABLE' ? 'bg-amber-400 border-white shadow-[0_0_8px_rgba(251,191,36,1)]' :
            toleranceResult.status === 'UNDERWEIGHT' || toleranceResult.status === 'OVERWEIGHT' ? 'bg-rose-500 border-white shadow-[0_0_8px_rgba(244,63,94,1)]' : 'bg-white border-slate-900'
          ]"
          :style="{ left: `${gaugePercent}%` }"
        ></div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Product, ScaleReading, ScaleStatus } from '../../../../types/api';
import type { ScaleToleranceResult } from '../../utils/scaleTolerance';

const { t } = useI18n();

const props = defineProps<{
  scaleReading: ScaleReading;
  scaleStatus: ScaleStatus;
  isAgentOnline: boolean;
  toleranceResult: ScaleToleranceResult;
  selectedProduct: Product | null;
  isPrinting?: boolean;
}>();

const formatWeight = (val?: number) => {
  if (val === undefined || val === null) return '0.000';
  return val.toFixed(3);
};

const gaugePercent = computed(() => {
  if (!props.isAgentOnline || !props.scaleStatus.connected) return 50;
  const min = props.selectedProduct?.min_weight ?? 0.150;
  const max = props.selectedProduct?.max_weight ?? 0.200;
  const range = max - min;
  if (range <= 0) return 50;

  const gaugeMin = min - 0.25 * range;
  const gaugeMax = max + 0.25 * range;
  const percent = ((props.scaleReading.weight - gaugeMin) / (gaugeMax - gaugeMin)) * 100;
  return Math.min(Math.max(percent, 2), 98);
});
</script>
