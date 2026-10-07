<template>
  <div 
    v-if="show" 
    class="fixed inset-0 z-50 flex items-center justify-center p-3 md:p-6 bg-slate-900/60 backdrop-blur-sm animate-in fade-in"
  >
    <div class="bg-white rounded-3xl shadow-2xl max-w-4xl w-full max-h-[90vh] border border-slate-100 flex flex-col overflow-hidden">
      <!-- Modal Header -->
      <div class="px-6 py-4 border-b border-slate-100 flex items-center justify-between shrink-0 bg-slate-50/50">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600 shadow-xs">
            <i class="fas fa-boxes-stacked text-lg"></i>
          </div>
          <div>
            <div class="flex items-center gap-2">
              <h2 class="font-black text-base md:text-lg text-slate-900 leading-tight">
                Danh Sách Thùng Đã Đóng
              </h2>
              <span class="px-2 py-0.5 rounded text-xs font-mono font-bold bg-indigo-100 text-indigo-800">
                {{ jobOrder }}
              </span>
            </div>
            <p class="text-xs text-slate-500 mt-0.5">
              Sản phẩm: <span class="font-bold text-slate-700">{{ product?.item_name || 'N/A' }}</span>
              <span v-if="product?.packed_qty" class="ml-1.5 text-slate-400">({{ product.packed_qty }} PCS/thùng)</span>
            </p>
          </div>
        </div>

        <div class="flex items-center gap-2">
          <button 
            @click="fetchCartons" 
            :disabled="isLoading"
            class="px-3 py-1.5 rounded-xl bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 text-xs font-bold transition-all flex items-center gap-1.5 shadow-xs cursor-pointer disabled:opacity-50"
            title="Tải lại danh sách"
          >
            <i :class="['fas fa-rotate-right', isLoading ? 'fa-spin' : '']"></i>
            <span>Làm Mới</span>
          </button>
          <button 
            @click="$emit('close')" 
            title="Đóng (ESC)"
            class="w-9 h-9 flex items-center justify-center rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-500 hover:text-slate-800 transition-all cursor-pointer"
          >
            <i class="fas fa-times text-base"></i>
          </button>
        </div>
      </div>

      <!-- KPI Progress Summary Bar -->
      <div class="px-6 py-3 bg-indigo-50/40 border-b border-indigo-100/60 flex items-center justify-between gap-4 flex-wrap shrink-0 text-xs">
        <div class="flex items-center gap-6">
          <div>
            <span class="text-slate-400 font-bold block uppercase text-[10px]">Tiến Độ Thùng:</span>
            <span class="font-bold font-mono text-sm text-slate-800">
              {{ cartons.length }} / {{ plannedCartons }} Thùng
            </span>
          </div>
          <div class="border-l border-indigo-200/60 pl-4">
            <span class="text-slate-400 font-bold block uppercase text-[10px]">Sản Lượng:</span>
            <span class="font-bold font-mono text-sm text-slate-800">
              {{ totalPackedQty.toLocaleString() }} / {{ totalQty.toLocaleString() }} PCS
            </span>
          </div>
          <div class="border-l border-indigo-200/60 pl-4">
            <span class="text-slate-400 font-bold block uppercase text-[10px]">Tỷ Lệ Hoàn Thành:</span>
            <span :class="['font-black text-sm', cartons.length >= plannedCartons ? 'text-amber-600' : 'text-indigo-600']">
              {{ percentage }}%
            </span>
          </div>
        </div>

        <!-- Search Input -->
        <div class="relative min-w-[220px]">
          <i class="fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-xs"></i>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="Tìm kiếm mã thùng, PO, LOT..."
            class="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 font-medium"
          />
        </div>
      </div>

      <!-- Table Content Area -->
      <div class="flex-1 overflow-y-auto p-4 min-h-[260px]">
        <!-- Loading -->
        <div v-if="isLoading" class="h-48 flex flex-col items-center justify-center text-slate-400 gap-2">
          <i class="fas fa-spinner fa-spin text-2xl text-indigo-500"></i>
          <span class="text-xs font-semibold">Đang tải danh sách thùng...</span>
        </div>

        <!-- Error -->
        <div v-else-if="fetchError" class="p-4 bg-rose-50 border border-rose-200 rounded-2xl text-rose-700 text-xs flex items-center justify-between">
          <div class="flex items-center gap-2">
            <i class="fas fa-exclamation-circle text-rose-500 text-base"></i>
            <span>{{ fetchError }}</span>
          </div>
          <button @click="fetchCartons" class="px-2.5 py-1 bg-rose-600 text-white rounded-lg font-bold hover:bg-rose-700">Thử lại</button>
        </div>

        <!-- Empty State -->
        <div v-else-if="filteredCartons.length === 0" class="h-48 flex flex-col items-center justify-center text-slate-400 gap-2 text-center">
          <i class="fas fa-box-open text-3xl text-slate-300"></i>
          <p class="text-xs font-semibold">
            {{ searchQuery ? 'Không tìm thấy thùng nào khớp với từ khóa tìm kiếm.' : 'Chưa có thùng nào được đóng cho công lệnh này.' }}
          </p>
        </div>

        <!-- Cartons Table -->
        <table v-else class="w-full text-left border-collapse text-xs">
          <thead>
            <tr class="border-b border-slate-200 text-slate-400 uppercase text-[10px] font-bold tracking-wider">
              <th class="py-2 px-3 w-12 text-center">STT</th>
              <th class="py-2 px-3">Mã Thùng (Carton S/N)</th>
              <th class="py-2 px-3">Trọng Lượng</th>
              <th class="py-2 px-3">PO Number</th>
              <th class="py-2 px-3">Mã Số Lô (LOT)</th>
              <th class="py-2 px-3">Thời Gian Đóng</th>
              <th class="py-2 px-3 text-center">Trạng Thái</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr 
              v-for="(c, idx) in filteredCartons" 
              :key="c.id || c.carton_sn"
              class="hover:bg-indigo-50/30 transition-colors"
            >
              <td class="py-2.5 px-3 text-center font-mono text-slate-400 font-bold">
                {{ idx + 1 }}
              </td>
              <td class="py-2.5 px-3 font-mono font-bold text-slate-900 select-all">
                {{ c.carton_sn }}
              </td>
              <td class="py-2.5 px-3 font-mono text-slate-700 font-semibold">
                {{ c.weight ? `${Number(c.weight).toFixed(2)} kg` : '-' }}
              </td>
              <td class="py-2.5 px-3 font-mono text-slate-600">
                {{ c.po_number || '-' }}
              </td>
              <td class="py-2.5 px-3 font-mono text-slate-600">
                {{ c.lot_number || '-' }}
              </td>
              <td class="py-2.5 px-3 text-slate-500 font-mono">
                {{ formatDate(c.created_at) }}
              </td>
              <td class="py-2.5 px-3 text-center">
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                  {{ c.status || 'SUCCESS' }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Footer -->
      <div class="px-6 py-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 shrink-0">
        <span>Hiển thị {{ filteredCartons.length }} / {{ cartons.length }} thùng</span>
        <button
          type="button"
          @click="$emit('close')"
          class="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-900 text-white font-bold transition-all cursor-pointer shadow-xs"
        >
          Đóng [ESC]
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Carton, Product } from '../../../../types/api';
import historyApi from '../../../history/api';

const { t } = useI18n();

const props = defineProps<{
  show: boolean;
  jobOrder: string;
  product: Product | null;
  plannedCartons: number;
  totalQty: number;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
}>();

const cartons = ref<Carton[]>([]);
const isLoading = ref(false);
const fetchError = ref('');
const searchQuery = ref('');

const totalPackedQty = computed(() => {
  return cartons.value.length * (props.product?.packed_qty || 0);
});

const percentage = computed(() => {
  if (!props.plannedCartons || props.plannedCartons <= 0) return 0;
  return Math.min(100, Math.round((cartons.value.length / props.plannedCartons) * 100));
});

const filteredCartons = computed(() => {
  if (!searchQuery.value.trim()) return cartons.value;
  const q = searchQuery.value.toLowerCase().trim();
  return cartons.value.filter((c) => {
    return (
      (c.carton_sn && c.carton_sn.toLowerCase().includes(q)) ||
      (c.po_number && c.po_number.toLowerCase().includes(q)) ||
      (c.lot_number && c.lot_number.toLowerCase().includes(q))
    );
  });
});

const formatDate = (isoStr?: string) => {
  if (!isoStr) return '-';
  try {
    const d = new Date(isoStr);
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
  } catch {
    return isoStr;
  }
};

const fetchCartons = async () => {
  if (!props.jobOrder) return;
  isLoading.value = true;
  fetchError.value = '';
  try {
    const resp = await historyApi.getCartons({
      job_order: props.jobOrder,
      limit: 200,
    });
    // Sort chronological: oldest to newest
    const items = resp.data.items || [];
    cartons.value = [...items].reverse();
  } catch (err: any) {
    fetchError.value = err?.response?.data?.detail || 'Không thể tải danh sách thùng đã đóng.';
  } finally {
    isLoading.value = false;
  }
};

watch(
  () => props.show,
  (isShown) => {
    if (isShown) {
      searchQuery.value = '';
      fetchCartons();
    }
  },
  { immediate: true }
);

const handleKeyDown = (e: KeyboardEvent) => {
  if (props.show && e.key === 'Escape') {
    emit('close');
  }
};

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown);
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown);
});
</script>
