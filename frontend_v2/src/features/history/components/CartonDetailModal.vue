<template>
  <div v-if="carton" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
    <div class="bg-white rounded-3xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col overflow-hidden animate-in fade-in zoom-in duration-200 border border-slate-100">
      <!-- Sticky Header -->
      <div class="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-900 text-white shrink-0">
        <div>
          <h2 class="text-xl font-bold tracking-tight">{{ t('admin.carton_details') }}: {{ carton.carton_sn }}</h2>
          <p class="text-xs text-slate-400 mt-0.5">{{ t('admin.created_at') }}: {{ formatDate(carton.created_at) }}</p>
        </div>
        <button @click="$emit('close')" class="hover:bg-white/10 p-2 rounded-xl transition-colors cursor-pointer text-slate-400 hover:text-white">
          <X class="w-6 h-6" />
        </button>
      </div>
      
      <!-- Scrollable Content Container -->
      <div class="flex-1 overflow-y-auto p-6 space-y-6">
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 bg-slate-50 p-6 rounded-2xl border border-slate-100">
          <div class="space-y-1">
            <p class="text-[10px] font-bold text-slate-400 uppercase">{{ t('admin.product') }}</p>
            <p class="font-bold text-slate-900 text-sm">{{ carton.product?.item_name }}</p>
          </div>
          <div class="space-y-1">
            <p class="text-[10px] font-bold text-slate-400 uppercase">{{ t('admin.upc') }}</p>
            <p class="font-mono text-slate-900 text-sm">{{ carton.product?.upc || '-' }}</p>
          </div>
          <div v-if="carton.job_order" class="space-y-1">
            <p class="text-[10px] font-bold text-slate-400 uppercase">{{ t('packing.job_order') }}</p>
            <p class="font-bold text-indigo-600 text-sm">{{ carton.job_order }}</p>
          </div>
          <div v-if="carton.po_number" class="space-y-1">
            <p class="text-[10px] font-bold text-slate-400 uppercase">PO Number</p>
            <p class="font-bold text-indigo-600 text-sm">{{ carton.po_number }}</p>
          </div>
          <div v-if="carton.lot_number" class="space-y-1">
            <p class="text-[10px] font-bold text-slate-400 uppercase">Lot Number</p>
            <p class="font-bold text-indigo-600 text-sm">{{ carton.lot_number }}</p>
          </div>
          <div v-if="carton.weight !== undefined && carton.weight !== null" class="space-y-1">
            <p class="text-[10px] font-bold text-slate-400 uppercase">{{ t('admin.weight') }}</p>
            <p class="font-bold text-emerald-700 text-sm">{{ carton.weight.toFixed(3) }} kg</p>
          </div>
          <div v-if="carton.date_code" class="space-y-1">
            <p class="text-[10px] font-bold text-slate-400 uppercase">Date Code</p>
            <p class="font-mono text-slate-900 text-sm">{{ carton.date_code }}</p>
          </div>
          <div class="space-y-1">
            <p class="text-[10px] font-bold text-slate-400 uppercase">{{ t('admin.station_id_mac') }}</p>
            <p class="font-mono text-indigo-900 text-[10px]">{{ carton.station_id || '-' }}</p>
          </div>
        </div>

        <div>
          <div class="flex justify-between items-center mb-4">
            <h3 class="font-bold text-slate-700 flex items-center gap-2">
              <Box class="w-5 h-5 text-indigo-500" />
              {{ t('admin.detailed_sns', { count: cartonItems.length }) }}
            </h3>
          </div>
          
          <div class="rounded-2xl border border-slate-200 bg-white shadow-inner overflow-hidden">
            <div v-for="(item, idx) in cartonItems" :key="item.id" class="px-6 py-3 border-b border-slate-50 last:border-0 flex items-center hover:bg-indigo-50/30 transition-colors group">
              <div class="w-7 h-7 rounded-full bg-slate-100 flex items-center justify-center text-[10px] font-black text-slate-400 shrink-0 mr-4 group-hover:bg-indigo-100 group-hover:text-indigo-600 transition-colors">
                {{ idx + 1 }}
              </div>
              <span class="flex-1 font-mono text-sm font-medium text-slate-700">{{ item.item_sn }}</span>
              <CheckCircle2 class="w-4 h-4 text-green-500 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <div v-if="cartonItems.length === 0 && !isLoadingItems" class="p-8 text-center text-slate-400 text-xs italic">
              {{ t('admin.weight_packed_no_serial') }}
            </div>
            <div v-if="isLoadingItems" class="p-12 text-center">
              <div class="animate-spin w-6 h-6 border-2 border-indigo-500 border-t-transparent rounded-full mx-auto mb-2"></div>
              <p class="text-xs text-slate-400">{{ t('admin.loading_data') }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Sticky Footer -->
      <div class="p-6 border-t border-slate-100 flex justify-between shrink-0 bg-white">
        <button v-if="isAdmin" @click="$emit('delete', carton)" class="px-5 py-2.5 rounded-xl bg-rose-50 font-bold text-rose-600 hover:bg-rose-100 transition-colors flex items-center gap-2 cursor-pointer">
          <Trash2 class="w-4 h-4" />
          <span>{{ t('admin.delete_carton') }}</span>
        </button>
        <div v-else></div>
        <button @click="$emit('close')" class="px-6 py-2.5 rounded-xl bg-slate-100 font-bold text-slate-600 hover:bg-slate-200 transition-colors cursor-pointer">
          {{ t('admin.close_window') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { X, Box, CheckCircle2, Trash2 } from 'lucide-vue-next';
import type { Carton } from '../../../types/api';

defineProps<{
  carton: Carton | null;
  cartonItems: { id: number; item_sn: string }[];
  isLoadingItems: boolean;
  isAdmin: boolean;
}>();

defineEmits<{
  (e: 'close'): void;
  (e: 'delete', carton: Carton): void;
}>();

const { t } = useI18n();

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return d.toLocaleString('vi-VN', { hour12: false });
};
</script>
