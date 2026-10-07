<template>
  <div class="p-8">
    <!-- Header with Title & Export Actions -->
    <div class="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
      <div>
        <h1 class="text-3xl font-bold text-slate-900 flex items-center gap-3">
          <i class="fas fa-clipboard-list text-indigo-600"></i>
          <span>{{ t('admin.history') }}</span>
        </h1>
        <p class="text-slate-500 text-sm mt-1">{{ t('admin.history_subtitle') }}</p>
      </div>

      <!-- Export to Excel Button with Dropdown Menu -->
      <div class="relative">
        <button 
          @click="toggleExportMenu" 
          :disabled="isExporting"
          class="bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white px-5 py-2.5 rounded-xl font-bold flex items-center gap-2.5 shadow-lg shadow-emerald-200 transition-all cursor-pointer"
        >
          <div v-if="isExporting" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          <FileSpreadsheet v-else class="w-4 h-4" />
          <span>{{ isExporting ? t('admin.exporting_excel') : t('admin.export_excel_btn') }}</span>
          <ChevronDown class="w-4 h-4 opacity-70" />
        </button>

        <!-- Dropdown Menu -->
        <div v-if="showExportMenu && !isExporting" class="absolute right-0 mt-2 w-72 bg-white rounded-2xl shadow-xl border border-slate-100 py-2 z-50 animate-in fade-in zoom-in duration-150">
          <button @click="handleExport('summary')" class="w-full text-left px-4 py-3 hover:bg-slate-50 transition-colors flex items-start gap-3 cursor-pointer border-none bg-transparent">
            <div class="p-2 rounded-lg bg-emerald-50 text-emerald-600 mt-0.5"><FileSpreadsheet class="w-4 h-4" /></div>
            <div><p class="font-bold text-slate-800 text-sm m-0">{{ t('admin.export_summary') }}</p><span class="text-xs text-slate-400 block mt-0.5">{{ t('admin.export_summary_desc') }}</span></div>
          </button>
          <div class="border-t border-slate-100 my-1"></div>
          <button @click="handleExport('detailed')" class="w-full text-left px-4 py-3 hover:bg-slate-50 transition-colors flex items-start gap-3 cursor-pointer border-none bg-transparent">
            <div class="p-2 rounded-lg bg-indigo-50 text-indigo-600 mt-0.5"><Download class="w-4 h-4" /></div>
            <div><p class="font-bold text-slate-800 text-sm m-0">{{ t('admin.export_detailed') }}</p><span class="text-xs text-slate-400 block mt-0.5">{{ t('admin.export_detailed_desc') }}</span></div>
          </button>
        </div>
      </div>
    </div>

    <!-- Advanced Multi-dimensional Filter Bar -->
    <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-xs mb-6 space-y-4">
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <!-- Search Carton SN -->
        <div class="space-y-1.5">
          <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">{{ t('admin.find_sn') }}</label>
          <div class="relative">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4" />
            <input 
              v-model="filters.search" 
              type="text" 
              :placeholder="t('admin.find_sn_placeholder')" 
              class="w-full pl-9 pr-3 py-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none text-sm font-medium"
              @keyup.enter="fetchHistory(0)"
            >
          </div>
        </div>

        <!-- Date Range: From Date -->
        <div class="space-y-1.5">
          <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">{{ t('admin.start_date') }}</label>
          <div class="relative">
            <Calendar class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4 pointer-events-none" />
            <input 
              ref="startDateInputRef"
              v-model="filters.start_date" 
              type="date" 
              @change="dateError = false"
              :class="dateError && !filters.start_date ? 'border-rose-400 bg-rose-50/40 focus:ring-rose-400' : 'border-slate-200 focus:ring-indigo-500'"
              class="w-full pl-9 pr-3 py-2.5 rounded-xl border focus:ring-2 outline-none text-sm bg-white font-medium transition-colors"
            >
          </div>
        </div>

        <!-- Date Range: To Date -->
        <div class="space-y-1.5">
          <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">{{ t('admin.end_date') }}</label>
          <div class="relative">
            <Calendar class="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4 pointer-events-none" />
            <input 
              v-model="filters.end_date" 
              type="date" 
              @change="dateError = false"
              :class="dateError && !filters.end_date ? 'border-rose-400 bg-rose-50/40 focus:ring-rose-400' : 'border-slate-200 focus:ring-indigo-500'"
              class="w-full pl-9 pr-3 py-2.5 rounded-xl border focus:ring-2 outline-none text-sm bg-white font-medium transition-colors"
            >
          </div>
        </div>

        <!-- Customer Dropdown -->
        <div class="space-y-1.5">
          <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">{{ t('admin.customer') }}</label>
          <select 
            v-model="filters.customer_id" 
            @change="onCustomerChange"
            class="w-full p-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none text-sm bg-white font-medium"
          >
            <option :value="null">{{ t('admin.all_customers') }}</option>
            <option v-for="c in customers" :key="c.id" :value="c.id">{{ c.name }} ({{ c.code }})</option>
          </select>
        </div>
      </div>

      <!-- Bottom row filters -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 items-end">
        <div class="space-y-1.5">
          <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">{{ t('admin.product') }}</label>
          <select 
            v-model="filters.product_id" 
            class="w-full p-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none text-sm bg-white font-medium"
          >
            <option :value="null">{{ t('admin.all_products') }}</option>
            <option v-for="p in filteredProducts" :key="p.id" :value="p.id">{{ p.item_name }}</option>
          </select>
        </div>

        <div class="space-y-1.5">
          <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">Work Order / PO#</label>
          <input 
            v-model="filters.job_order" 
            type="text" 
            placeholder="JO-5544 / PO-4500..." 
            class="w-full p-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none text-sm font-medium"
            @keyup.enter="fetchHistory(0)"
          >
        </div>

        <div class="space-y-1.5">
          <label class="text-xs font-bold text-slate-500 uppercase tracking-wider">{{ t('admin.status') }}</label>
          <select 
            v-model="filters.status" 
            class="w-full p-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none text-sm bg-white font-medium"
          >
            <option :value="null">{{ t('admin.all_statuses') }}</option>
            <option value="SUCCESS">SUCCESS</option>
            <option value="FAILED">FAILED</option>
          </select>
        </div>

        <!-- Action Buttons -->
        <div class="flex gap-2">
          <button 
            @click="fetchHistory(0)" 
            :disabled="isLoading"
            class="flex-1 bg-indigo-600 text-white py-2.5 rounded-xl font-bold hover:bg-indigo-700 disabled:opacity-60 transition-colors shadow-sm flex items-center justify-center gap-2 cursor-pointer"
          >
            <div v-if="isLoading" class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
            <Filter v-else class="w-4 h-4" />
            <span>{{ t('admin.filter_data') }}</span>
          </button>
          <button 
            @click="resetFilters" 
            class="p-2.5 rounded-xl border border-slate-200 text-slate-500 hover:bg-slate-50 transition-colors cursor-pointer" 
            :title="t('common.reset')"
          >
            <RotateCcw class="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>

    <!-- Table -->
    <div class="bg-white rounded-2xl shadow-xs border border-slate-200 overflow-hidden">
      <table class="w-full text-left border-collapse">
        <thead>
          <tr class="bg-slate-50 border-b border-slate-200 text-xs uppercase tracking-wider text-slate-500 font-bold">
            <th class="p-4">{{ t('admin.created_at') }}</th>
            <th class="p-4">{{ t('admin.carton_sn') }}</th>
            <th class="p-4">{{ t('admin.product') }}</th>
            <th class="p-4">{{ t('packing.job_order') }}</th>
            <th class="p-4">PO#</th>
            <th class="p-4">Lot</th>
            <th class="p-4">{{ t('admin.weight') }}</th>
            <th class="p-4">{{ t('admin.status') }}</th>
            <th class="p-4">{{ t('admin.station_id') }}</th>
            <th class="p-4 text-right">{{ t('admin.details') }}</th>
          </tr>
        </thead>
        <tbody class="text-sm divide-y divide-slate-100">
          <template v-if="isLoading">
            <tr v-for="i in 6" :key="`sk-${i}`" class="animate-pulse">
              <td class="p-4"><div class="h-3.5 bg-slate-200 rounded w-24"></div></td>
              <td class="p-4"><div class="h-3.5 bg-slate-200 rounded w-36"></div></td>
              <td class="p-4"><div class="h-3.5 bg-slate-200 rounded w-28 mb-1"></div><div class="h-2.5 bg-slate-100 rounded w-16"></div></td>
              <td class="p-4"><div class="h-3.5 bg-slate-200 rounded w-20"></div></td>
              <td class="p-4"><div class="h-3.5 bg-slate-200 rounded w-20"></div></td>
              <td class="p-4"><div class="h-3.5 bg-slate-200 rounded w-20"></div></td>
              <td class="p-4"><div class="h-3.5 bg-slate-200 rounded w-16"></div></td>
              <td class="p-4"><div class="h-5 bg-slate-200 rounded-full w-14"></div></td>
              <td class="p-4"><div class="h-3.5 bg-slate-200 rounded w-12"></div></td>
              <td class="p-4 text-right"><div class="h-8 bg-slate-100 rounded-lg w-20 ml-auto"></div></td>
            </tr>
          </template>

          <template v-else>
            <tr v-for="carton in history" :key="carton.id" class="hover:bg-slate-50 transition-colors">
              <td class="p-4 text-slate-500 font-mono text-xs">{{ formatDate(carton.created_at) }}</td>
              <td class="p-4 font-bold text-indigo-900 font-mono">
                <div class="flex items-center gap-2">
                  <span>{{ carton.carton_sn }}</span>
                  <span v-if="carton.is_reprint" class="bg-amber-100 text-amber-700 text-[9px] px-1.5 py-0.5 rounded font-black uppercase tracking-tighter">{{ t('print.reprint') }}</span>
                  <span v-else class="bg-emerald-100 text-emerald-700 text-[9px] px-1.5 py-0.5 rounded font-black uppercase tracking-tighter">Bản gốc</span>
                </div>
              </td>
              <td class="p-4">
                <div class="font-bold text-slate-700">{{ carton.product?.item_name || 'N/A' }}</div>
                <div class="text-[11px] text-slate-400">{{ getCustomerName(carton.product) }}</div>
              </td>
              <td class="p-4 text-slate-600 font-mono text-xs">{{ carton.job_order || '-' }}</td>
              <td class="p-4 text-slate-600 font-mono text-xs">{{ carton.po_number || '-' }}</td>
              <td class="p-4 text-slate-600 font-mono text-xs">{{ carton.lot_number || '-' }}</td>
              <td class="p-4 text-slate-600 font-mono text-xs">
                <span v-if="carton.weight !== null && carton.weight !== undefined" class="font-bold text-emerald-700">{{ carton.weight.toFixed(3) }} kg</span>
                <span v-else class="text-slate-300">-</span>
              </td>
              <td class="p-4">
                <span :class="['px-2.5 py-1 rounded-full text-[10px] font-black tracking-wider', carton.status === 'SUCCESS' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700']">{{ carton.status }}</span>
              </td>
              <td class="p-4 text-[11px] font-mono text-slate-400">{{ carton.station_id || '-' }}</td>
              <td class="p-4 text-right">
                <div class="flex justify-end gap-1.5">
                  <button @click="viewDetail(carton)" class="p-2 text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors cursor-pointer" :title="t('admin.details')"><ExternalLink class="w-4 h-4" /></button>
                  <button v-if="authStore.isAdmin" @click="handleReprint(carton)" :disabled="reprintingCartonId === carton.id" class="p-2 text-amber-600 hover:bg-amber-50 rounded-lg transition-colors cursor-pointer disabled:opacity-50" :title="t('print.reprint')"><RotateCcw class="w-4 h-4" :class="{ 'animate-spin': reprintingCartonId === carton.id }" /></button>
                  <button v-if="authStore.isAdmin" @click="handleDelete(carton)" class="p-2 text-rose-600 hover:bg-rose-50 rounded-lg transition-colors cursor-pointer" :title="t('admin.delete_carton')"><Trash2 class="w-4 h-4" /></button>
                </div>
              </td>
            </tr>
            <tr v-if="history.length === 0">
              <td colspan="10" class="p-12 text-center text-slate-400 italic">{{ t('admin.no_data') }}</td>
            </tr>
          </template>
        </tbody>
      </table>

      <!-- Pagination -->
      <div class="p-4 bg-slate-50 border-t border-slate-200 flex justify-between items-center">
        <span class="text-xs text-slate-500 font-medium">{{ t('admin.showing_records', { current: history.length, total: totalCount }) }}</span>
        <div class="flex gap-2">
          <button @click="fetchHistory(currentPage - 1)" :disabled="currentPage === 0 || isLoading" class="px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 disabled:opacity-30 hover:bg-slate-50 text-xs font-semibold cursor-pointer">{{ t('admin.previous') }}</button>
          <button @click="fetchHistory(currentPage + 1)" :disabled="(currentPage + 1) * 50 >= totalCount || isLoading" class="px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-slate-600 disabled:opacity-30 hover:bg-slate-50 text-xs font-semibold cursor-pointer">{{ t('admin.next') }}</button>
        </div>
      </div>
    </div>

    <!-- Detail Modal -->
    <CartonDetailModal 
      :carton="selectedCarton"
      :carton-items="cartonItems"
      :is-loading-items="isLoadingItems"
      :is-admin="authStore.isAdmin"
      @close="selectedCarton = null"
      @delete="handleDelete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { 
  Search, Filter, ExternalLink, Trash2, FileSpreadsheet, 
  Download, ChevronDown, Calendar, RotateCcw 
} from 'lucide-vue-next';
import CartonDetailModal from '../../features/history/components/CartonDetailModal.vue';
import historyApi from '../../features/history/api';
import catalogApi from '../../features/catalog/api';
import { useSystemStore } from '../../core/stores/system';
import { useSettingsStore } from '../../core/stores/settings';
import { displayLocale } from '../../i18n/locale';
import { useAuthStore } from '../../core/stores/auth';
import { useAdminReprint } from '../../features/print/composables/useAdminReprint';
import type { Carton, Product, Customer } from '../../types/api';

const { t } = useI18n();
const settings = useSettingsStore();
const system = useSystemStore();
const authStore = useAuthStore();
const history = ref<Carton[]>([]);
const products = ref<Product[]>([]);
const customers = ref<Customer[]>([]);
const totalCount = ref<number>(0);
const currentPage = ref<number>(0);
const selectedCarton = ref<Carton | null>(null);
const cartonItems = ref<{ id: number, item_sn: string }[]>([]);
const isLoadingItems = ref<boolean>(false);
const isLoading = ref<boolean>(false);
const isExporting = ref<boolean>(false);
const showExportMenu = ref<boolean>(false);
const startDateInputRef = ref<HTMLInputElement | null>(null);
const dateError = ref<boolean>(false);

interface HistoryFilters {
  search: string; customer_id: number | null; product_id: number | null;
  status: string | null; start_date: string; end_date: string; job_order: string;
}
const initFilters = (): HistoryFilters => ({
  search: '', customer_id: null, product_id: null, status: null, start_date: '', end_date: '', job_order: ''
});
const filters = ref<HistoryFilters>(initFilters());
const filteredProducts = computed(() => {
  if (!filters.value.customer_id) return products.value;
  return products.value.filter(p => p.customer_id === filters.value.customer_id);
});

const onCustomerChange = () => {
  if (filters.value.product_id) {
    const prod = products.value.find(p => p.id === filters.value.product_id);
    if (prod && prod.customer_id !== filters.value.customer_id) filters.value.product_id = null;
  }
  fetchHistory(0);
};

const resetFilters = () => {
  filters.value = initFilters();
  fetchHistory(0);
};

const fetchHistory = async (page: number = 0) => {
  isLoading.value = true;
  try {
    currentPage.value = page;
    const res = await historyApi.getCartons({
      skip: page * 50,
      limit: 50,
      search: filters.value.search || undefined,
      customer_id: filters.value.customer_id || undefined,
      product_id: filters.value.product_id || undefined,
      status: filters.value.status || undefined,
      start_date: filters.value.start_date || undefined,
      end_date: filters.value.end_date || undefined,
      job_order: filters.value.job_order || undefined,
      po_number: filters.value.job_order || undefined
    });
    history.value = res.data.items;
    totalCount.value = res.data.total;
  } catch (err) {
    system.showNotification(t('admin.history_load_failed'), 'error');
  } finally {
    isLoading.value = false;
  }
};

const { reprintingCartonId, handleReprint } = useAdminReprint(() => fetchHistory(currentPage.value));

const fetchCatalogData = async () => {
  try {
    const [pRes, cRes] = await Promise.all([
      catalogApi.getAllProducts(),
      catalogApi.getCustomers()
    ]);
    products.value = pRes.data;
    customers.value = cRes.data;
  } catch (err) {
    console.error('Failed to load products/customers for history filters:', err);
  }
};

const validateDateRangeForExport = (): boolean => {
  if (!filters.value.start_date || !filters.value.end_date) {
    dateError.value = true;
    startDateInputRef.value?.focus();
    system.showNotification(t('admin.export_dates_required'), 'warning');
    return false;
  }
  if (filters.value.start_date > filters.value.end_date) {
    dateError.value = true;
    startDateInputRef.value?.focus();
    system.showNotification(t('admin.export_dates_invalid'), 'warning');
    return false;
  }
  return true;
};

const toggleExportMenu = () => {
  if (!validateDateRangeForExport()) return;
  showExportMenu.value = !showExportMenu.value;
};

const handleExport = async (mode: 'summary' | 'detailed') => {
  showExportMenu.value = false;
  if (!validateDateRangeForExport()) return;

  try {
    isExporting.value = true;
    system.showNotification(t('admin.export_initializing'), 'info');

    const params: Record<string, any> = {
      search: filters.value.search || undefined,
      customer_id: filters.value.customer_id || undefined,
      product_id: filters.value.product_id || undefined,
      status: filters.value.status || undefined,
      start_date: filters.value.start_date || undefined,
      end_date: filters.value.end_date || undefined,
      job_order: filters.value.job_order || undefined,
      po_number: filters.value.job_order || undefined
    };

    const res = await historyApi.exportCartons(params, mode);
    const blob = new Blob([res.data], { 
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' 
    });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const nowStr = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    a.download = `carton_export_${mode}_${nowStr}.xlsx`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    system.showNotification(t('admin.export_success'), 'success');
  } catch (err) {
    system.showNotification(t('admin.export_failed'), 'error');
  } finally {
    isExporting.value = false;
  }
};

const viewDetail = async (carton: Carton) => {
  selectedCarton.value = carton;
  cartonItems.value = [];
  isLoadingItems.value = true;
  try {
    const res = await historyApi.getCartonDetail(carton.id);
    cartonItems.value = res.data.items || [];
  } catch (err) {
    system.showNotification(t('admin.items_load_failed'), 'error');
  } finally {
    isLoadingItems.value = false;
  }
};

const handleDelete = async (carton: Carton) => {
  if (!confirm(t('admin.delete_carton_confirm', { sn: carton.carton_sn }))) {
    return;
  }
  
  try {
    await historyApi.deleteCarton(carton.id);
    system.showNotification(t('admin.delete_carton_success'), 'success');
    if (selectedCarton.value?.id === carton.id) {
      selectedCarton.value = null;
    }
    fetchHistory(currentPage.value);
  } catch (err) {
    system.showNotification(t('admin.delete_carton_failed'), 'error');
  }
};

const getCustomerName = (product?: Product) => {
  if (product?.customer?.name) return product.customer.name;
  if (product?.customer_id) {
    const c = customers.value.find(item => item.id === product.customer_id);
    if (c) return c.name;
  }
  return '';
};

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  return d.toLocaleString(displayLocale(settings.language));
};

onMounted(() => {
  fetchHistory();
  fetchCatalogData();
});

watch([() => filters.value.product_id, () => filters.value.status, () => filters.value.start_date, () => filters.value.end_date], () => {
  fetchHistory(0);
});
</script>
