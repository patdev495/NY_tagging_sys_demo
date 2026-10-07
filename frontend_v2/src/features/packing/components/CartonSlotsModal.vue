<template>
  <div v-if="show" class="fixed inset-0 bg-slate-900/75 flex justify-center items-center z-[2000] p-3 md:p-6" role="dialog" aria-modal="true">
    <div class="w-full max-w-[860px] bg-white rounded-xl overflow-hidden shadow-2xl flex flex-col border border-slate-300 max-h-[90vh]">
      <!-- Header -->
      <div class="flex justify-between items-center px-5 py-3.5 border-b border-slate-200 bg-slate-50">
        <div class="flex items-center gap-2.5">
          <div class="w-8 h-8 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center font-bold">
            <i class="fas fa-boxes-stacked text-sm"></i>
          </div>
          <div>
            <h2 class="m-0 text-base font-black text-slate-900 leading-tight">
              {{ t('packing.carton_slots_title', 'Sơ Đồ Vị Trí Thùng') }}
            </h2>
            <p class="m-0 text-xs text-slate-500">
              {{ t('packing.slots_summary', { jobOrder, total: totalCartons }) }}
            </p>
          </div>
        </div>
        <button 
          @click="$emit('close')" 
          class="w-8 h-8 rounded-lg bg-white hover:bg-slate-200 border border-slate-300 flex items-center justify-center text-slate-600 hover:text-slate-900 cursor-pointer transition-colors"
          :title="t('packing.close_title')"
        >
          <i class="fas fa-times text-sm"></i>
        </button>
      </div>

      <!-- Legend & Progress Summary -->
      <div class="px-5 py-2.5 bg-slate-100/70 border-b border-slate-200 flex flex-wrap justify-between items-center gap-3 text-xs">
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-1.5">
            <span class="w-3 h-3 rounded bg-emerald-600 border border-emerald-700 inline-block"></span>
            <span class="font-semibold text-slate-700">{{ t('packing.completed', { count: scannedCount }) }}</span>
          </div>
          <div class="flex items-center gap-1.5">
            <span class="w-3 h-3 rounded bg-blue-50 border-2 border-blue-600 inline-block"></span>
            <span class="font-semibold text-slate-700">{{ t('packing.selected') }}</span>
          </div>
          <div class="flex items-center gap-1.5">
            <span class="w-3 h-3 rounded bg-white border border-slate-300 inline-block"></span>
            <span class="font-semibold text-slate-700">{{ t('packing.pending', { count: (totalCartons || 0) - (scannedCount || 0) }) }}</span>
          </div>
        </div>

        <div class="text-xs font-bold text-slate-700">
          {{ t('packing.progress', { current: scannedCount, total: totalCartons }) }}
        </div>
      </div>

      <!-- Slots Grid (Carton Matrix) -->
      <div class="p-5 overflow-y-auto flex-1 bg-slate-50/40">
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
          <div
            v-for="slot in slots"
            :key="slot.id"
            @click="handleSlotClick(slot)"
            class="slot-card relative p-3 rounded-lg text-center cursor-pointer border transition-all flex flex-col justify-between min-h-[76px] shadow-xs active:scale-98"
            :class="[
              slot.status === 'SCANNED'
                ? 'bg-emerald-50/90 border-emerald-300 text-emerald-950 hover:bg-emerald-100/90'
                : (selectedSlotId === slot.id 
                    ? 'bg-blue-50 border-2 border-blue-600 ring-2 ring-blue-500/20 text-blue-900 font-extrabold'
                    : 'bg-white border-slate-300 text-slate-800 hover:border-blue-400 hover:bg-blue-50/40')
            ]"
            :title="slot.status === 'SCANNED' ? t('packing.slot_scanned_title') : t('packing.slot_select_title')"
          >
            <!-- Top badge: Status or checkmark -->
            <div class="flex items-center justify-between w-full mb-1">
              <span class="text-[11px] font-extrabold px-1.5 py-0.2 rounded" :class="slot.status === 'SCANNED' ? 'bg-emerald-200 text-emerald-900' : 'bg-slate-100 text-slate-600'">
                {{ t('packing.carton_number', { number: slot.carton_number }) }}
              </span>
              <i v-if="slot.status === 'SCANNED'" class="fas fa-check-circle text-emerald-600 text-sm"></i>
              <span v-else-if="selectedSlotId === slot.id" class="text-[9px] uppercase font-bold text-blue-700 bg-blue-100 px-1 rounded">Active</span>
            </div>

            <!-- Carton SN -->
            <span class="font-barcode-mono text-xs sm:text-sm font-bold tracking-tight block truncate select-all" :title="slot.carton_sn">
              {{ slot.carton_sn }}
            </span>

            <!-- Bottom subtext -->
            <span class="text-[10px] text-slate-500 font-medium block mt-1">
              {{ slot.status === 'SCANNED' ? t('packing.label_printed') : t('packing.ready_to_pack') }}
            </span>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-5 py-3 bg-slate-100 border-t border-slate-200 flex justify-between items-center">
        <span class="text-xs text-slate-500 font-medium">{{ t('packing.slots_hint') }}</span>
        <button 
          @click="$emit('close')" 
          class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-1.5 px-5 rounded-lg transition-colors cursor-pointer text-xs"
        >
          {{ t('settings.close') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import type { JobOrderSlot } from '../../../types/api';

const props = defineProps<{
  show: boolean;
  jobOrder: string;
  totalCartons?: number;
  scannedCount?: number;
  slots: JobOrderSlot[];
  selectedSlotId?: number | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'selectSlot', slot: JobOrderSlot): void;
}>();

const { t } = useI18n();

const handleSlotClick = (slot: JobOrderSlot) => {
  emit('selectSlot', slot);
};
</script>
