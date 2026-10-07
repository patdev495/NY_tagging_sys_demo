<template>
  <div class="p-6 md:p-8 space-y-6 max-w-7xl mx-auto animate-in">
    <!-- Header Toolbar -->
    <div class="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
      <div>
        <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">Quản Lý Đợt Sản Xuất</h1>
        <p class="text-sm text-slate-500 mt-1">Theo dõi tiến độ đóng gói theo Work Order và Đợt cân đóng hàng (PO / Lot).</p>
      </div>

      <div class="flex flex-wrap items-center gap-3">
        <!-- Tab Selector -->
        <div class="inline-flex p-1 bg-slate-100 rounded-xl border border-slate-200 text-xs font-semibold">
          <button
            @click="activeTab = 'job_orders'"
            :class="['px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-2', activeTab === 'job_orders' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-600 hover:text-slate-900']"
          >
            <span>Work Orders</span>
            <span class="px-1.5 py-0.2 rounded-full text-[10px] font-mono" :class="activeTab === 'job_orders' ? 'bg-indigo-50 text-indigo-700' : 'bg-slate-200 text-slate-600'">{{ jobOrders.length }}</span>
          </button>
          <button
            @click="activeTab = 'po_runs'"
            :class="['px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-2', activeTab === 'po_runs' ? 'bg-white text-indigo-600 shadow-sm' : 'text-slate-600 hover:text-slate-900']"
          >
            <span>Đợt PO & Lot (Erro)</span>
            <span class="px-1.5 py-0.2 rounded-full text-[10px] font-mono" :class="activeTab === 'po_runs' ? 'bg-indigo-50 text-indigo-700' : 'bg-slate-200 text-slate-600'">{{ poRuns.length }}</span>
          </button>
        </div>

        <!-- Refresh Button -->
        <button
          @click="loadData" :disabled="isLoading"
          class="inline-flex items-center gap-2 px-3.5 py-1.5 bg-white border border-slate-300 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-all shadow-sm active:scale-95 disabled:opacity-50"
        >
          <RefreshCw :class="['w-4 h-4 text-slate-500', isLoading ? 'animate-spin text-indigo-600' : '']" />
          <span>{{ isLoading ? 'Đang tải...' : 'Làm mới' }}</span>
        </button>
        <button
          v-if="authStore.isAdmin"
          data-testid="open-slot-cancellation"
          @click="openCancellationModal"
          class="inline-flex items-center gap-2 px-3.5 py-1.5 bg-rose-600 border border-rose-700 rounded-xl text-xs font-semibold text-white hover:bg-rose-700 transition-all shadow-sm active:scale-95"
        >
          <Trash2 class="w-4 h-4" />
          <span>Xoá cấp phát công lệnh</span>
        </button>
      </div>
    </div>

    <!-- Slot Allocation Cancellation Modal -->
    <div v-if="showCancellationModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
      <div class="bg-white w-full max-w-lg rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
        <div class="p-6 border-b border-slate-100 flex items-start justify-between">
          <div>
            <h3 class="text-xl font-bold text-slate-900">Kiểm tra huỷ cấp phát</h3>
            <p class="text-xs text-slate-500 mt-1">Chỉ xoá được công lệnh chưa có thùng nào được quét.</p>
          </div>
          <button @click="closeCancellationModal" class="p-2 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100">
            <X class="w-5 h-5" />
          </button>
        </div>

        <div class="p-6 space-y-4">
          <label class="block text-xs font-bold text-slate-700 uppercase tracking-wide" for="cancellation-job-order">Mã công lệnh</label>
          <div class="flex gap-2">
            <input
              id="cancellation-job-order"
              data-testid="cancellation-job-order-input"
              v-model.trim="cancellationJobOrder"
              @keyup.enter="checkCancellation"
              placeholder="Ví dụ: 1257157"
              class="min-w-0 flex-1 rounded-xl border border-slate-300 px-3 py-2 text-sm font-mono font-semibold outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
            />
            <button
              data-testid="check-slot-cancellation"
              @click="checkCancellation"
              :disabled="isCheckingCancellation || !cancellationJobOrder"
              class="px-3.5 py-2 rounded-xl bg-indigo-600 text-white text-xs font-bold hover:bg-indigo-700 disabled:opacity-50"
            >{{ isCheckingCancellation ? 'Đang kiểm tra...' : 'Kiểm tra' }}</button>
          </div>

          <p v-if="cancellationError" class="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-xs font-medium text-rose-700">{{ cancellationError }}</p>

          <div v-if="cancellationCheck" class="rounded-xl border p-4 space-y-3" :class="cancellationCheck.can_cancel ? 'border-amber-200 bg-amber-50' : 'border-slate-200 bg-slate-50'">
            <div class="flex justify-between text-sm"><span class="text-slate-600">Slot đã cấp</span><strong class="font-mono text-slate-900">{{ cancellationCheck.total_slots }}</strong></div>
            <div class="flex justify-between text-sm"><span class="text-slate-600">Thùng đã quét</span><strong class="font-mono" :class="cancellationCheck.scanned_slots > 0 ? 'text-rose-700' : 'text-emerald-700'">{{ cancellationCheck.scanned_slots }}</strong></div>
            <p v-if="cancellationCheck.total_slots === 0" class="text-xs font-medium text-slate-600">Công lệnh này chưa được cấp slot.</p>
            <p v-else-if="!cancellationCheck.can_cancel" class="text-xs font-medium text-rose-700">Không thể xoá vì công lệnh đã có thùng được quét hoặc xuất kho.</p>
            <p v-else class="text-xs font-medium text-amber-800">Toàn bộ {{ cancellationCheck.total_slots }} slot chưa được quét và sẽ bị xoá vĩnh viễn.</p>
          </div>
        </div>

        <div class="p-4 border-t border-slate-100 bg-slate-50 flex justify-end gap-2">
          <button @click="closeCancellationModal" :disabled="isCancelling" class="px-4 py-2 bg-white border border-slate-300 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-100 disabled:opacity-50">Đóng</button>
          <button
            v-if="cancellationCheck?.can_cancel"
            data-testid="confirm-slot-cancellation"
            @click="cancelSlotAllocation"
            :disabled="isCancelling"
            class="px-4 py-2 bg-rose-600 text-white rounded-xl text-xs font-bold hover:bg-rose-700 disabled:opacity-50"
          >{{ isCancelling ? 'Đang xoá...' : `Xác nhận xoá ${cancellationCheck.total_slots} slot` }}</button>
        </div>
      </div>
    </div>

    <!-- Search Box -->
    <div class="bg-white p-4 rounded-xl shadow-sm border border-slate-200 flex items-center gap-3">
      <Search class="w-4 h-4 text-slate-400 shrink-0" />
      <input
        v-model="searchQuery"
        type="text"
        :placeholder="activeTab === 'job_orders' ? 'Tìm theo Mã Work Order, Tên Sản Phẩm, Khách Hàng...' : 'Tìm theo PO Number, Lot Number, Sản Phẩm...'"
        class="w-full text-sm outline-none bg-transparent placeholder:text-slate-400"
      />
      <span v-if="searchQuery" @click="searchQuery = ''" class="cursor-pointer text-xs text-slate-400 hover:text-slate-600">Xóa</span>
    </div>

    <!-- Tab 1: Job Orders Table -->
    <div v-if="activeTab === 'job_orders'" class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
      <div class="p-5 border-b border-slate-100 flex items-center justify-between">
        <h2 class="text-base font-bold text-slate-900">Danh Sách Work Order Đã Cấp Phát Slot</h2>
        <span class="text-xs text-slate-400">{{ filteredJobOrders.length }} Work Order</span>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm">
          <thead class="bg-slate-50 text-slate-500 text-xs uppercase font-semibold border-b border-slate-100">
            <tr>
              <th class="py-3.5 px-4">Mã Work Order</th>
              <th class="py-3.5 px-4">Khách Hàng</th>
              <th class="py-3.5 px-4">Sản Phẩm</th>
              <th class="py-3.5 px-4 min-w-[200px]">Tiến Độ Đóng Thùng</th>
              <th class="py-3.5 px-4 text-center">Đã Quét / Chờ</th>
              <th class="py-3.5 px-4 text-center">Xuất Kho</th>
              <th class="py-3.5 px-4">Quét Gần Nhất</th>
              <th class="py-3.5 px-4 text-center">Thao Tác</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-if="filteredJobOrders.length === 0">
              <td colspan="8" class="py-12 text-center text-slate-400 text-sm">Không tìm thấy Work Order nào.</td>
            </tr>
            <tr v-for="jo in filteredJobOrders" :key="jo.job_order" class="hover:bg-slate-50/80 transition-colors">
              <td class="py-3.5 px-4 font-mono font-bold text-indigo-700">{{ jo.job_order }}</td>
              <td class="py-3.5 px-4"><span class="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-xs font-semibold">{{ jo.customer_code }}</span></td>
              <td class="py-3.5 px-4 font-medium text-slate-800">{{ jo.product_name }}</td>
              <td class="py-3.5 px-4">
                <div class="space-y-1">
                  <div class="flex items-center justify-between text-xs font-mono">
                    <span class="text-slate-600 font-bold">{{ jo.scanned_slots }} / {{ jo.total_slots }} thùng</span>
                    <span :class="['font-bold', jo.completion_rate === 100 ? 'text-emerald-600' : 'text-indigo-600']">{{ jo.completion_rate }}%</span>
                  </div>
                  <div class="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      :class="['h-full rounded-full transition-all duration-300', jo.completion_rate === 100 ? 'bg-emerald-500' : 'bg-indigo-600']"
                      :style="{ width: `${jo.completion_rate}%` }"
                    ></div>
                  </div>
                </div>
              </td>
              <td class="py-3.5 px-4 text-center font-mono text-xs">
                <span class="text-emerald-600 font-bold">{{ jo.scanned_slots }}</span> / <span class="text-slate-400">{{ jo.pending_slots }}</span>
              </td>
              <td class="py-3.5 px-4 text-center font-mono text-xs">
                <span :class="jo.shipped_slots > 0 ? 'px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 font-bold' : 'text-slate-400'">{{ jo.shipped_slots }}</span>
              </td>
              <td class="py-3.5 px-4 text-xs text-slate-500 whitespace-nowrap">{{ formatDateTime(jo.latest_scan_at) }}</td>
              <td class="py-3.5 px-4 text-center">
                <button
                  @click="openSlotsModal(jo)"
                  class="inline-flex items-center gap-1.5 px-3 py-1 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 rounded-lg text-xs font-semibold transition-colors"
                >
                  <Eye class="w-3.5 h-3.5" />
                  <span>Chi tiết Slots</span>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Tab 2: PO / Lot Runs Table -->
    <div v-if="activeTab === 'po_runs'" class="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
      <div class="p-5 border-b border-slate-100 flex items-center justify-between">
        <h2 class="text-base font-bold text-slate-900">Danh Sách Đợt Cân Đóng Hàng (PO & Lot)</h2>
        <span class="text-xs text-slate-400">{{ filteredPoRuns.length }} đợt đóng hàng</span>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left text-sm">
          <thead class="bg-slate-50 text-slate-500 text-xs uppercase font-semibold border-b border-slate-100">
            <tr>
              <th class="py-3.5 px-4">PO Number</th>
              <th class="py-3.5 px-4">Lot Number</th>
              <th class="py-3.5 px-4">Khách Hàng</th>
              <th class="py-3.5 px-4">Sản Phẩm</th>
              <th class="py-3.5 px-4 text-center">Date Code</th>
              <th class="py-3.5 px-4 text-center">Tổng Số Thùng</th>
              <th class="py-3.5 px-4 text-center">Tổng Khối Lượng</th>
              <th class="py-3.5 px-4">Đóng Gần Nhất</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-if="filteredPoRuns.length === 0">
              <td colspan="8" class="py-12 text-center text-slate-400 text-sm">Không tìm thấy đợt PO & Lot nào.</td>
            </tr>
            <tr v-for="run in filteredPoRuns" :key="run.po_number + run.lot_number" class="hover:bg-slate-50/80 transition-colors">
              <td class="py-3.5 px-4 font-mono font-bold text-indigo-700">{{ run.po_number }}</td>
              <td class="py-3.5 px-4 font-mono font-semibold text-slate-800">{{ run.lot_number }}</td>
              <td class="py-3.5 px-4"><span class="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-xs font-semibold">{{ run.customer_code }}</span></td>
              <td class="py-3.5 px-4 font-medium text-slate-800">{{ run.product_name }}</td>
              <td class="py-3.5 px-4 text-center font-mono text-xs text-slate-600">{{ run.date_code || '—' }}</td>
              <td class="py-3.5 px-4 text-center font-mono">
                <span class="px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 text-xs font-bold">{{ run.total_cartons }} thùng</span>
              </td>
              <td class="py-3.5 px-4 text-center font-mono font-bold text-slate-900">{{ run.total_weight.toFixed(2) }} kg</td>
              <td class="py-3.5 px-4 text-xs text-slate-500 whitespace-nowrap">{{ formatDateTime(run.latest_packed_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Slots Details Modal -->
    <div v-if="showSlotsModal && selectedJO" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
      <div class="bg-white w-full max-w-4xl rounded-2xl shadow-xl border border-slate-200 flex flex-col max-h-[90vh] overflow-hidden animate-in">
        <!-- Modal Header -->
        <div class="p-6 border-b border-slate-100 flex items-start justify-between">
          <div>
            <div class="flex items-center gap-3">
              <h3 class="text-xl font-bold text-slate-900">Chi Tiết Slots — {{ selectedJO.job_order }}</h3>
              <span class="px-2.5 py-0.5 rounded-full text-xs font-bold bg-indigo-50 text-indigo-700">{{ selectedJO.completion_rate }}% Hoàn thành</span>
            </div>
            <p class="text-xs text-slate-500 mt-1">{{ selectedJO.product_name }} ({{ selectedJO.customer_code }}) — Tổng {{ selectedJO.total_slots }} slot thùng</p>
          </div>
          <button @click="closeSlotsModal" class="p-2 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100">
            <X class="w-5 h-5" />
          </button>
        </div>

        <!-- Modal Stats Summary -->
        <div class="grid grid-cols-3 gap-3 p-4 bg-slate-50 border-b border-slate-100 text-xs font-semibold text-center">
          <div class="p-2 bg-white rounded-lg border border-slate-200">
            <span class="text-slate-400 block">Đã Quét</span>
            <span class="text-base font-bold text-emerald-600 font-mono">{{ selectedJO.scanned_slots }}</span>
          </div>
          <div class="p-2 bg-white rounded-lg border border-slate-200">
            <span class="text-slate-400 block">Chờ Quét</span>
            <span class="text-base font-bold text-slate-500 font-mono">{{ selectedJO.pending_slots }}</span>
          </div>
          <div class="p-2 bg-white rounded-lg border border-slate-200">
            <span class="text-slate-400 block">Đã Xuất Kho</span>
            <span class="text-base font-bold text-blue-600 font-mono">{{ selectedJO.shipped_slots }}</span>
          </div>
        </div>

        <!-- Modal Slots Table -->
        <div class="flex-1 overflow-y-auto p-4">
          <div v-if="isLoadingSlots" class="py-12 text-center text-slate-400 text-sm">Đang tải danh sách slots...</div>
          <table v-else class="w-full text-left text-sm">
            <thead class="bg-slate-100 text-slate-500 text-xs uppercase font-semibold sticky top-0">
              <tr>
                <th class="py-2.5 px-3 text-center">Thùng #</th>
                <th class="py-2.5 px-3">Mã Carton SN</th>
                <th class="py-2.5 px-3 text-center">Trạng Thái</th>
                <th class="py-2.5 px-3 text-center">Xuất Kho</th>
                <th class="py-2.5 px-3">Thời Gian Quét</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100 font-mono text-xs">
              <tr v-for="slot in slotsList" :key="slot.id" class="hover:bg-slate-50">
                <td class="py-2.5 px-3 text-center font-bold text-slate-700">#{{ slot.carton_number }}</td>
                <td class="py-2.5 px-3 font-semibold text-indigo-900">{{ slot.carton_sn }}</td>
                <td class="py-2.5 px-3 text-center">
                  <span
                    :class="[
                      'px-2 py-0.5 rounded-full font-bold',
                      slot.status === 'SCANNED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-500'
                    ]"
                  >
                    {{ slot.status === 'SCANNED' ? 'Đã đóng' : 'Chờ quét' }}
                  </span>
                </td>
                <td class="py-2.5 px-3 text-center">
                  <span v-if="slot.shipped === 1" class="px-2 py-0.5 rounded-full font-bold bg-blue-50 text-blue-700 border border-blue-200">Đã xuất</span>
                  <span v-else class="text-slate-300">—</span>
                </td>
                <td class="py-2.5 px-3 text-slate-500 font-sans">{{ formatDateTime(slot.scanned_at) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Modal Footer -->
        <div class="p-4 border-t border-slate-100 bg-slate-50 flex justify-end">
          <button @click="closeSlotsModal" class="px-4 py-2 bg-white border border-slate-300 rounded-xl text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors shadow-sm">
            Đóng cửa sổ
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { Search, RefreshCw, Eye, Trash2, X } from 'lucide-vue-next';
import { useI18n } from 'vue-i18n';
import { useAuthStore } from '../../core/stores/auth';
import {
  cancelJobOrderSlotAllocation,
  checkJobOrderSlotCancellation,
  fetchJobOrdersSummary,
  fetchJobOrderSlots,
  fetchPOLotRuns,
  type JobOrderSummary,
  type JobOrderSlotDetail,
  type JobOrderSlotCancellationCheck,
  type POLotRunSummary,
} from '../../features/production_run/api';

const { t } = useI18n();
const authStore = useAuthStore();

const activeTab = ref<'job_orders' | 'po_runs'>('job_orders');
const searchQuery = ref<string>('');
const isLoading = ref<boolean>(false);

const jobOrders = ref<JobOrderSummary[]>([]);
const poRuns = ref<POLotRunSummary[]>([]);

// Slots modal state
const showSlotsModal = ref<boolean>(false);
const selectedJO = ref<JobOrderSummary | null>(null);
const slotsList = ref<JobOrderSlotDetail[]>([]);
const isLoadingSlots = ref<boolean>(false);
const showCancellationModal = ref(false);
const cancellationJobOrder = ref('');
const cancellationCheck = ref<JobOrderSlotCancellationCheck | null>(null);
const cancellationError = ref('');
const isCheckingCancellation = ref(false);
const isCancelling = ref(false);

const filteredJobOrders = computed(() => {
  if (!searchQuery.value.trim()) return jobOrders.value;
  const q = searchQuery.value.toLowerCase().trim();
  return jobOrders.value.filter(
    (jo) =>
      jo.job_order.toLowerCase().includes(q) ||
      jo.product_name.toLowerCase().includes(q) ||
      jo.customer_code.toLowerCase().includes(q)
  );
});

const filteredPoRuns = computed(() => {
  if (!searchQuery.value.trim()) return poRuns.value;
  const q = searchQuery.value.toLowerCase().trim();
  return poRuns.value.filter(
    (r) =>
      r.po_number.toLowerCase().includes(q) ||
      r.lot_number.toLowerCase().includes(q) ||
      r.product_name.toLowerCase().includes(q) ||
      r.customer_code.toLowerCase().includes(q)
  );
});

function formatDateTime(dtStr: string | null): string {
  if (!dtStr) return '—';
  const d = new Date(dtStr);
  return d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) +
    ' ' + d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' });
}

async function loadData() {
  isLoading.value = true;
  try {
    const [jos, runs] = await Promise.all([fetchJobOrdersSummary(), fetchPOLotRuns()]);
    jobOrders.value = jos;
    poRuns.value = runs;
  } catch (error) {
    console.error('Failed to load production runs:', error);
  } finally {
    isLoading.value = false;
  }
}

async function openSlotsModal(jo: JobOrderSummary) {
  selectedJO.value = jo;
  showSlotsModal.value = true;
  isLoadingSlots.value = true;
  slotsList.value = [];
  try {
    slotsList.value = await fetchJobOrderSlots(jo.job_order);
  } catch (error) {
    console.error('Failed to load job order slots:', error);
  } finally {
    isLoadingSlots.value = false;
  }
}

function closeSlotsModal() {
  showSlotsModal.value = false;
  selectedJO.value = null;
  slotsList.value = [];
}

function openCancellationModal() {
  showCancellationModal.value = true;
  cancellationJobOrder.value = '';
  cancellationCheck.value = null;
  cancellationError.value = '';
}

function closeCancellationModal(force = false) {
  if (isCancelling.value && !force) return;
  showCancellationModal.value = false;
}

async function checkCancellation() {
  if (!cancellationJobOrder.value || isCheckingCancellation.value) return;
  isCheckingCancellation.value = true;
  cancellationCheck.value = null;
  cancellationError.value = '';
  try {
    cancellationCheck.value = await checkJobOrderSlotCancellation(cancellationJobOrder.value);
  } catch (error: any) {
    cancellationError.value = error?.response?.data?.detail || 'Không thể kiểm tra cấp phát công lệnh.';
  } finally {
    isCheckingCancellation.value = false;
  }
}

async function cancelSlotAllocation() {
  if (!cancellationCheck.value?.can_cancel || isCancelling.value) return;
  isCancelling.value = true;
  cancellationError.value = '';
  try {
    await cancelJobOrderSlotAllocation(cancellationCheck.value.job_order);
    closeCancellationModal(true);
    await loadData();
  } catch (error: any) {
    cancellationError.value = error?.response?.data?.detail || 'Không thể xoá cấp phát công lệnh.';
  } finally {
    isCancelling.value = false;
  }
}

onMounted(() => {
  loadData();
});
</script>

<style scoped>
.animate-in { animation: fadeIn 0.25s ease-out; }
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
