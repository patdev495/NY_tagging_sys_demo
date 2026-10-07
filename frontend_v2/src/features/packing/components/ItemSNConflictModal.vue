<template>
  <div v-if="show && conflict" class="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4" role="dialog" aria-modal="true">
    <section class="w-full max-w-2xl overflow-hidden rounded-2xl bg-white shadow-2xl">
      <header class="flex items-start justify-between gap-4 bg-rose-700 px-5 py-4 text-white">
        <div>
          <h2 class="text-lg font-black">Mã sê-ri con đã thuộc thùng khác</h2>
          <p class="mt-1 font-mono text-sm text-rose-100">{{ conflict.item_sn }}</p>
        </div>
        <button class="rounded-lg p-2 hover:bg-white/15" title="Đóng" @click="$emit('close')">✕</button>
      </header>
      <div class="max-h-[65vh] overflow-y-auto p-5">
        <p class="mb-4 text-sm text-slate-600">Chỉ tra cứu. Người phụ trách quyết định bước xử lý tiếp theo.</p>
        <article v-for="carton in conflict.conflicts" :key="carton.id" class="mb-3 rounded-xl border border-slate-200 p-4 last:mb-0">
          <div class="flex items-start justify-between gap-3">
            <div>
              <p class="font-mono text-base font-black text-slate-900">{{ carton.carton_sn }}</p>
              <p class="mt-1 text-sm font-semibold text-slate-700">{{ carton.product_name || '—' }}</p>
            </div>
            <span class="rounded bg-slate-100 px-2 py-1 text-xs font-bold text-slate-700">{{ carton.status || '—' }}</span>
          </div>
          <dl class="mt-3 grid grid-cols-2 gap-x-4 gap-y-2 text-xs text-slate-600">
            <div><dt class="font-bold text-slate-500">Work Order</dt><dd>{{ carton.job_order || '—' }}</dd></div>
            <div><dt class="font-bold text-slate-500">Trạm</dt><dd>{{ carton.station_id || '—' }}</dd></div>
            <div><dt class="font-bold text-slate-500">Thời điểm đóng</dt><dd>{{ formatDate(carton.created_at) }}</dd></div>
            <div><dt class="font-bold text-slate-500">Số mã trong thùng</dt><dd>{{ carton.items_count }}</dd></div>
          </dl>
          <button class="mt-3 text-xs font-bold text-blue-700 hover:underline" @click="toggleDetails(carton.id)">
            {{ expandedId === carton.id ? 'Ẩn danh sách mã' : 'Xem các mã trong thùng' }}
          </button>
          <p v-if="loadingId === carton.id" class="mt-2 text-xs text-slate-500">Đang tải…</p>
          <ul v-else-if="details[carton.id]" class="mt-2 max-h-32 overflow-y-auto rounded bg-slate-50 p-2 font-mono text-xs text-slate-700">
            <li v-for="item in details[carton.id]" :key="item.id" :class="item.item_sn === conflict.item_sn ? 'font-black text-rose-700' : ''">{{ item.item_sn }}</li>
          </ul>
        </article>
      </div>
      <footer class="flex justify-end border-t border-slate-100 p-4"><button class="rounded-lg bg-slate-800 px-4 py-2 text-sm font-bold text-white" @click="$emit('close')">Đóng</button></footer>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import historyApi from '../../history/api';
import type { ItemSNConflictResponse } from '../../../types/api';

const props = defineProps<{ show: boolean; conflict: ItemSNConflictResponse | null }>();
defineEmits<{ (event: 'close'): void }>();
const expandedId = ref<number | null>(null);
const loadingId = ref<number | null>(null);
const details = ref<Record<number, { id: number; item_sn: string }[]>>({});

const formatDate = (value?: string | null) => value ? new Date(value).toLocaleString() : '—';
const toggleDetails = async (cartonId: number) => {
  if (expandedId.value === cartonId) { expandedId.value = null; return; }
  expandedId.value = cartonId;
  if (details.value[cartonId]) return;
  loadingId.value = cartonId;
  try { details.value[cartonId] = (await historyApi.getCartonDetail(cartonId)).data.items || []; }
  finally { loadingId.value = null; }
};
</script>
