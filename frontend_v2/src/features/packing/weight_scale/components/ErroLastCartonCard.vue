<template>
  <div class="flex flex-col h-full gap-2 min-h-0 justify-between">
    <!-- Compact Session Packaging Counter -->
    <div class="px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 shadow-xs flex items-center justify-between shrink-0">
      <div>
        <span class="text-[10px] font-bold uppercase tracking-wider text-slate-400">{{ t('erro.current_session_progress') }}</span>
        <div class="flex items-baseline gap-1.5 mt-0.5">
          <span class="text-3xl font-black text-slate-900 font-mono leading-none">{{ sessionPackedCount }}</span>
          <span class="text-xs font-bold text-slate-500">{{ t('erro.carton_count_with_pieces', { count: sessionPackedCount * (selectedProduct?.packed_qty || 190) }) }}</span>
        </div>
      </div>
      
      <button 
        @click="$emit('reset-session')" 
        class="px-2 py-1 rounded bg-slate-50 hover:bg-rose-50 text-[11px] text-slate-400 hover:text-rose-600 transition-colors border border-slate-200 hover:border-rose-200 cursor-pointer flex items-center gap-1 font-bold"
        :title="t('erro.reset_counter')"
      >
        <i class="fas fa-redo"></i> {{ t('common.reset') }}
      </button>
    </div>

    <!-- Last Carton Print Result Card (Scrollable Body) -->
    <div class="p-3.5 rounded-xl bg-white border border-slate-200 shadow-xs flex-1 flex flex-col min-h-0 overflow-hidden">
      <div class="flex items-center justify-between pb-2 border-b border-slate-100 mb-2 shrink-0">
        <div class="flex items-center gap-1.5">
          <i class="fas fa-box text-indigo-500"></i>
          <span class="font-bold text-xs text-slate-900">{{ t('erro.last_printed_carton') }}</span>
        </div>
        <span 
          v-if="lastPackedCarton"
          class="px-1.5 py-0.5 rounded text-[9px] font-black uppercase tracking-wider bg-emerald-100 text-emerald-800"
        >
          {{ lastPackedCarton.status || 'SUCCESS' }}
        </span>
      </div>

      <div v-if="lastPackedCarton" class="flex-1 min-h-0 flex flex-col justify-between text-xs">
        <div class="space-y-2 overflow-y-auto pr-1">
          <div>
            <span class="text-[10px] text-slate-400 font-bold uppercase">{{ t('erro.carton_serial_number') }}</span>
            <p class="font-mono font-bold text-xs text-indigo-900 bg-indigo-50/60 p-1.5 rounded border border-indigo-100 select-all truncate mt-0.5">
              {{ lastPackedCarton.carton_sn }}
            </p>
          </div>

          <div class="grid grid-cols-2 gap-1.5">
            <div class="bg-slate-50 p-1.5 rounded border border-slate-100">
              <span class="text-[10px] text-slate-400 font-bold uppercase block">{{ t('erro.weight') }}</span>
              <p class="font-mono font-bold text-emerald-700 text-xs">
                {{ lastPackedCarton.weight ? lastPackedCarton.weight.toFixed(3) : '-' }} kg
              </p>
            </div>
            <div class="bg-slate-50 p-1.5 rounded border border-slate-100">
              <span class="text-[10px] text-slate-400 font-bold uppercase block">Date Code:</span>
              <p class="font-mono font-bold text-slate-700 text-xs">
                {{ lastPackedCarton.date_code || '-' }}
              </p>
            </div>
          </div>

          <div class="grid grid-cols-2 gap-1.5">
            <div class="bg-slate-50 p-1.5 rounded border border-slate-100">
              <span class="text-[10px] text-slate-400 font-bold uppercase block">PO Number:</span>
              <p class="font-mono font-semibold text-slate-700 text-xs truncate">
                {{ lastPackedCarton.po_number || '-' }}
              </p>
            </div>
            <div class="bg-slate-50 p-1.5 rounded border border-slate-100">
              <span class="text-[10px] text-slate-400 font-bold uppercase block">Lot Number:</span>
              <p class="font-mono font-semibold text-slate-700 text-xs truncate">
                {{ lastPackedCarton.lot_number || '-' }}
              </p>
            </div>
          </div>

          <div class="text-[11px] text-slate-400 flex items-center justify-between pt-1">
            <span>{{ t('erro.time') }}</span>
            <span class="text-slate-600 font-medium">{{ formatDateTime(lastPackedCarton.created_at) }}</span>
          </div>
        </div>
      </div>

      <!-- Empty State for Last Carton -->
      <div v-else class="flex-1 flex flex-col items-center justify-center text-center p-4 text-slate-400">
        <i class="fas fa-inbox text-2xl mb-1 opacity-30"></i>
        <p class="text-xs">{{ t('erro.no_cartons_this_session') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import type { Product, Carton } from '../../../../types/api';
import i18n from '../../../../i18n';
import { displayLocale } from '../../../../i18n/locale';

const { t } = useI18n();

defineProps<{
  sessionPackedCount: number;
  selectedProduct: Product | null;
  lastPackedCarton: Carton | null;
  isPrinting?: boolean;
}>();

defineEmits<{
  (e: 'reset-session'): void;
}>();

const formatDateTime = (dateStr?: string) => {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  const locale = displayLocale(i18n.global.locale.value);
  return d.toLocaleTimeString(locale) + ' ' + d.toLocaleDateString(locale);
};
</script>
