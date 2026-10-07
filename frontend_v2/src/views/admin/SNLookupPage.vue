<template>
  <div class="p-8 max-w-4xl mx-auto">
    <div class="text-center mb-12">
      <h1 class="text-4xl font-black text-slate-900 tracking-tight mb-4">{{ t('admin.sn_lookup') }}</h1>
      <p class="text-slate-500 text-lg">{{ t('admin.sn_lookup_subtitle') }}</p>
    </div>

    <!-- Search Input Area -->
    <div class="bg-white p-8 rounded-3xl shadow-xl border border-slate-100 mb-8 transform transition-all hover:shadow-2xl">
      <form @submit.prevent="handleSearch" class="relative">
        <Search class="absolute left-4 top-1/2 -translate-y-1/2 text-indigo-500 w-6 h-6" />
        <input 
          v-model="searchQuery"
          type="text" 
          :placeholder="t('admin.sn_lookup_placeholder')" 
          class="w-full pl-14 pr-32 py-5 rounded-2xl border-2 border-slate-100 focus:border-indigo-500 focus:ring-4 focus:ring-indigo-500/10 outline-none text-xl font-mono transition-all"
          :disabled="isSearching"
          ref="searchInput"
        >
        <button 
          type="submit" 
          :disabled="isSearching || !searchQuery"
          class="absolute right-3 top-1/2 -translate-y-1/2 bg-indigo-600 text-white px-6 py-3 rounded-xl font-bold hover:bg-indigo-700 transition-all disabled:opacity-50 shadow-lg shadow-indigo-200"
        >
          {{ isSearching ? t('admin.searching') : t('admin.search') }}
        </button>
      </form>
      <div class="mt-4 flex gap-4 text-xs font-medium text-slate-400 px-2">
        <span>{{ t('admin.tip_sn') }}</span>
      </div>
    </div>

    <!-- Result Area -->
    <div v-if="result" class="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div class="bg-white rounded-3xl shadow-xl border border-slate-100 overflow-hidden">
        <!-- Result Header -->
        <div class="bg-indigo-900 p-8 text-white">
          <div class="flex justify-between items-start mb-6">
            <div>
              <span class="bg-indigo-500 text-[10px] font-black uppercase tracking-widest px-2 py-1 rounded mb-2 inline-block">{{ t('admin.result_found') }}</span>
              <h2 class="text-3xl font-bold">{{ t('admin.carton') }}: {{ result.carton_sn }}</h2>
            </div>
            <div :class="['px-4 py-2 rounded-xl font-black text-sm', result.status === 'SUCCESS' ? 'bg-green-500' : 'bg-red-500']">
              {{ result.status }}
            </div>
          </div>
          
          <div class="grid grid-cols-2 md:grid-cols-4 gap-6 opacity-90 text-sm">
            <div>
              <p class="text-indigo-300 font-bold uppercase text-[10px] mb-1">{{ t('admin.packed_at') }}</p>
              <p>{{ formatDate(result.created_at) }}</p>
            </div>
            <div>
              <p class="text-indigo-300 font-bold uppercase text-[10px] mb-1">{{ t('packing.job_order') }}</p>
              <p>{{ result.job_order || 'N/A' }}</p>
            </div>
            <div>
              <p class="text-indigo-300 font-bold uppercase text-[10px] mb-1">{{ t('admin.packed_by') }}</p>
              <p>{{ result.packed_by || 'System' }}</p>
            </div>
            <div>
              <p class="text-indigo-300 font-bold uppercase text-[10px] mb-1">{{ t('admin.origin') }}</p>
              <p>{{ result.carton_origin || 'VN' }}</p>
            </div>
          </div>
        </div>

        <!-- Product Info -->
        <div class="p-8 border-b border-slate-50 flex items-center gap-6">
          <div class="bg-indigo-50 p-4 rounded-2xl">
            <Package class="w-10 h-10 text-indigo-600" />
          </div>
          <div class="flex-1">
            <p class="text-xs font-bold text-slate-400 uppercase mb-1">{{ t('admin.product_info') }}</p>
            <h3 class="text-xl font-bold text-slate-900">{{ result.product?.item_name }}</h3>
            <p class="text-slate-500 font-mono text-sm">{{ t('admin.upc') }}: {{ result.product?.upc || '-' }}</p>
          </div>
        </div>

        <!-- Items inside -->
        <div class="p-8">
          <div class="flex justify-between items-center mb-4">
            <h4 class="font-bold text-slate-700 flex items-center gap-2">
              <ClipboardList class="w-5 h-5 text-indigo-500" />
              {{ t('admin.items_in_carton', { count: result.items?.length || 0 }) }}
            </h4>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-80 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-slate-200 scrollbar-track-transparent rounded-xl p-1">
            <div 
              v-for="item in result.items" 
              :key="item.id" 
              :class="['p-3 rounded-xl border transition-all text-sm font-mono flex items-center justify-between', item.item_sn === searchQuery ? 'bg-indigo-600 border-indigo-600 text-white shadow-lg shadow-indigo-200 z-10' : 'bg-slate-50 border-slate-100 text-slate-600']"
            >
              <span>{{ item.item_sn }}</span>
              <Check v-if="item.item_sn === searchQuery" class="w-4 h-4" />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Empty State -->
    <div v-else-if="hasSearched && !isSearching" class="text-center p-12 bg-slate-50 rounded-3xl border-2 border-dashed border-slate-200 animate-in fade-in duration-300">
      <div class="bg-white w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4 shadow-sm">
        <AlertCircle class="w-8 h-8 text-slate-300" />
      </div>
      <h3 class="text-xl font-bold text-slate-700 mb-2">{{ t('admin.product_not_found') }}</h3>
      <p class="text-slate-400 max-w-sm mx-auto">{{ t('admin.sn_not_exist', { sn: searchQuery }) }}</p>
    </div>

    <!-- Initial State -->
    <div v-else-if="!hasSearched" class="grid grid-cols-1 md:grid-cols-3 gap-6 opacity-50">
      <div class="p-6 text-center border border-slate-200 rounded-2xl">
        <div class="bg-slate-100 w-10 h-10 rounded-full flex items-center justify-center mx-auto mb-3">
          <Zap class="w-5 h-5 text-slate-400" />
        </div>
        <p class="text-xs font-bold text-slate-600 uppercase mb-1">{{ t('admin.high_speed') }}</p>
        <p class="text-[10px] text-slate-400">{{ t('admin.high_speed_desc') }}</p>
      </div>
      <div class="p-6 text-center border border-slate-200 rounded-2xl">
        <div class="bg-slate-100 w-10 h-10 rounded-full flex items-center justify-center mx-auto mb-3">
          <ShieldCheck class="w-5 h-5 text-slate-400" />
        </div>
        <p class="text-xs font-bold text-slate-600 uppercase mb-1">{{ t('admin.accurate') }}</p>
        <p class="text-[10px] text-slate-400">{{ t('admin.accurate_desc') }}</p>
      </div>
      <div class="p-6 text-center border border-slate-200 rounded-2xl">
        <div class="bg-slate-100 w-10 h-10 rounded-full flex items-center justify-center mx-auto mb-3">
          <Link class="w-5 h-5 text-slate-400" />
        </div>
        <p class="text-xs font-bold text-slate-600 uppercase mb-1">{{ t('admin.linked') }}</p>
        <p class="text-[10px] text-slate-400">{{ t('admin.linked_desc') }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { 
  Search, 
  Package, 
  ClipboardList, 
  Check, 
  AlertCircle, 
  Zap, 
  ShieldCheck, 
  Link 
} from 'lucide-vue-next';
import historyApi from '../../features/history/api';
import { useSystemStore } from '../../core/stores/system';
import { useSettingsStore } from '../../core/stores/settings';
import { displayLocale } from '../../i18n/locale';
import type { Carton, Product } from '../../types/api';

const { t } = useI18n();
const settings = useSettingsStore();
const system = useSystemStore();
const searchQuery = ref<string>('');
const isSearching = ref<boolean>(false);
const hasSearched = ref<boolean>(false);

interface SearchResult extends Carton {
  product?: Product;
  items?: { id: number, item_sn: string }[];
  packed_by?: string;
}

const result = ref<SearchResult | null>(null);
const searchInput = ref<HTMLInputElement | null>(null);

const handleSearch = async () => {
  if (!searchQuery.value) return;
  
  isSearching.value = true;
  hasSearched.value = true;
  result.value = null;
  
  try {
    const res = await historyApi.searchByItemSN(searchQuery.value.trim());
    result.value = res.data;
  } catch (err: any) {
    if (err.response?.status !== 404) {
      system.showNotification('System error during search', 'error');
    }
  } finally {
    isSearching.value = false;
  }
};

const formatDate = (dateStr: string) => {
  const d = new Date(dateStr);
  return d.toLocaleString(displayLocale(settings.language));
};

onMounted(() => {
  if (searchInput.value) searchInput.value.focus();
});
</script>
