<template>
  <div v-if="show" class="fixed inset-0 bg-black/60 backdrop-blur-sm flex justify-center items-center z-[2000]" @click.self="$emit('close')">
    <div class="w-[95%] max-w-[600px] max-h-[90vh] bg-white rounded-[24px] overflow-hidden shadow-2xl flex flex-col animate-in">
      <div class="flex justify-between items-center px-8 pt-6 pb-4">
        <div class="flex items-center gap-3 text-slate-800"><i class="fas fa-search text-[1.5rem] text-blue-600"></i><h2 class="m-0 text-[1.5rem] font-bold">{{ t('print.emergency_title') }}</h2></div>
        <button @click="$emit('close')" class="bg-slate-100 border-none w-9 h-9 rounded-xl text-slate-500 cursor-pointer flex items-center justify-center transition-all hover:bg-slate-200 hover:text-slate-900 hover:rotate-90"><i class="fas fa-times"></i></button>
      </div>
      <div class="px-8 pb-8 overflow-y-auto">
        <p class="text-slate-500 text-[0.95rem] mb-6">{{ t('print.emergency_hint') }}</p>
        <div class="border border-slate-200 rounded-xl p-1.5 flex gap-2 bg-white mb-8 focus-within:border-blue-500 focus-within:ring-4 focus-within:ring-blue-500/10">
          <div class="flex-1 flex items-center pl-3"><i class="fas fa-barcode text-slate-400 text-[1.1rem]"></i>
            <input v-model="searchSN" :placeholder="t('print.emergency_placeholder')" @keyup.enter="handleSearch" class="w-full border-none px-3.5 py-3 text-[1rem] text-slate-800 outline-none bg-transparent" />
          </div>
          <button @click="handleSearch" :disabled="loading" class="bg-blue-600 text-white border-none px-6 rounded-lg font-semibold cursor-pointer flex items-center gap-2 hover:bg-blue-700 disabled:bg-slate-400 disabled:cursor-not-allowed">
            <i class="fas fa-spinner fa-spin" v-if="loading"></i><span v-else>{{ t('admin.search') }}</span>
          </button>
        </div>
        <div v-if="result" class="bg-slate-50 border border-slate-200 rounded-2xl overflow-hidden animate-in">
          <div class="px-5 py-4 bg-white border-b border-slate-200 flex items-center gap-3"><div class="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_0_4px_rgba(16,185,129,0.1)]"></div><h3 class="m-0 text-[1.2rem] text-slate-900 font-mono">{{ result.carton_sn }}</h3><span class="ml-auto rounded-full bg-emerald-50 px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-emerald-700">Bản gốc</span></div>
          <div class="p-5">
            <div class="flex flex-col gap-1"><span class="text-[0.75rem] uppercase tracking-wider text-slate-500 font-semibold">{{ t('admin.product') }}</span><span class="text-slate-800 font-medium text-[0.95rem]">{{ result?.product?.item_name || 'N/A' }}</span></div>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-4 mt-4">
              <div v-if="result?.job_order" class="flex flex-col gap-1"><span class="text-[0.75rem] uppercase tracking-wider text-slate-500 font-semibold">{{ t('packing.job_order') }}</span><span class="text-slate-800 font-medium text-[0.95rem]">{{ result?.job_order }}</span></div>
              <div v-if="result?.po_number" class="flex flex-col gap-1"><span class="text-[0.75rem] uppercase tracking-wider text-slate-500 font-semibold">PO Number</span><span class="text-slate-800 font-medium text-[0.95rem]">{{ result?.po_number }}</span></div>
              <div v-if="result?.lot_number" class="flex flex-col gap-1"><span class="text-[0.75rem] uppercase tracking-wider text-slate-500 font-semibold">Lot Number</span><span class="text-slate-800 font-medium text-[0.95rem]">{{ result?.lot_number }}</span></div>
              <div v-if="result?.weight !== undefined && result?.weight !== null" class="flex flex-col gap-1"><span class="text-[0.75rem] uppercase tracking-wider text-slate-500 font-semibold">{{ t('admin.weight') }}</span><span class="text-emerald-700 font-bold text-[0.95rem]">{{ result.weight.toFixed(3) }} kg</span></div>
              <div v-if="result?.date_code" class="flex flex-col gap-1"><span class="text-[0.75rem] uppercase tracking-wider text-slate-500 font-semibold">Date Code</span><span class="text-slate-800 font-mono text-[0.95rem]">{{ result?.date_code }}</span></div>
              <div class="flex flex-col gap-1"><span class="text-[0.75rem] uppercase tracking-wider text-slate-500 font-semibold">{{ t('admin.date') }}</span><span class="text-slate-800 font-medium text-[0.95rem]">{{ result ? new Date(result.created_at).toLocaleString() : '-' }}</span></div>
            </div>
            <div v-if="result.print_history?.length" class="mt-5 border-t border-slate-200 pt-4">
              <p class="mb-2 text-[0.75rem] font-semibold uppercase tracking-wider text-slate-500">Lịch sử in lại ({{ result.print_history.length }})</p>
              <ul class="max-h-40 space-y-2 overflow-y-auto pr-1" aria-label="Lịch sử in lại">
                <li v-for="attempt in result.print_history" :key="`${attempt.created_at}-${attempt.status}`" class="flex items-center justify-between gap-3 rounded-lg border border-amber-100 bg-amber-50 px-3 py-2 text-xs">
                  <span class="font-semibold text-amber-900">In lại</span>
                  <span class="text-slate-600">{{ new Date(attempt.created_at).toLocaleString() }}</span>
                  <span class="rounded bg-white px-1.5 py-0.5 font-medium text-slate-700">{{ attempt.status }}</span>
                </li>
              </ul>
            </div>
          </div>
          <div class="px-5 py-4 bg-white border-t border-slate-200 flex justify-end gap-3">
            <button v-if="result?.product?.packing_mode !== 'weight_scale'" @click="$emit('rescan', result)" class="bg-slate-100 text-slate-600 border border-slate-200 px-5 py-3 rounded-xl font-semibold cursor-pointer flex items-center gap-2 mr-auto transition-colors hover:bg-slate-200 hover:text-slate-900">
              <i class="fas fa-redo"></i><span>{{ t('print.rescan_items') }}</span>
            </button>
            <button v-if="canStationReprint" @click="$emit('reprint', result)" :disabled="loading || isReprinting" class="bg-slate-900 text-white border-none px-6 py-3 rounded-xl font-semibold cursor-pointer flex items-center gap-2.5 transition-all hover:bg-black hover:-translate-y-0.5 disabled:opacity-70 disabled:cursor-not-allowed ml-auto">
              <i class="fas fa-spinner fa-spin" v-if="loading || isReprinting"></i><i class="fas fa-print" v-else></i><span>{{ t('print.print_label') }}</span>
            </button>
            <p v-else class="ml-auto text-xs text-slate-500">{{ t('print.erro_reprint_admin_only') }}</p>
          </div>
        </div>
        <div v-else-if="searchSN && !loading && searched" class="text-center p-10 bg-slate-50 rounded-2xl border border-dashed border-slate-300 animate-in">
          <div class="text-[3rem] text-slate-300 mb-4"><i class="fas fa-box-open"></i></div><p class="text-slate-500 m-0">{{ t('print.no_carton_found') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import printApi from '../api';
import { useSystemStore } from '../../../core/stores/system';
import type { Carton } from '../../../types/api';

const { t } = useI18n();

defineProps<{
  show: boolean;
  isReprinting?: boolean;
}>();

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'reprint', carton: Carton): void
  (e: 'rescan', carton: Carton): void
}>();

const system = useSystemStore();
const searchSN = ref<string>('');
const result = ref<Carton | null>(null);
const loading = ref<boolean>(false);
const searched = ref<boolean>(false);
const canStationReprint = computed(() => result.value?.product?.customer?.code?.toUpperCase() === 'UI');

const handleSearch = async () => {
  if (!searchSN.value) return;
  loading.value = true; result.value = null; searched.value = false;
  try {
    const res = await printApi.searchCarton(searchSN.value.trim());
    if (res.data) result.value = res.data;
    else system.showNotification(t('print.no_carton_found'), 'warning');
  } catch (err: any) { 
    system.showNotification(t('print.search_failed', { error: err.response?.data?.detail || err.message }), 'error'); 
  }
  finally { loading.value = false; searched.value = true; }
};
</script>
