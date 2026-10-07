<template>
  <div class="min-h-screen w-full p-4 md:p-8 flex items-center justify-center bg-slate-100 text-slate-900 relative select-none">
    
    <!-- Top-right system controls -->
    <div class="absolute top-4 right-4 md:top-6 md:right-8 z-10 flex items-center gap-2">
      <LanguageSwitch variant="header" />
      <button
        type="button"
        @click="showSettings = true"
        class="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-white border border-slate-300 text-slate-700 hover:text-blue-700 hover:border-blue-400 font-bold text-xs shadow-xs transition-colors"
        :title="t('home.settingsTitle')"
      >
        <i class="fas fa-cog text-blue-600 text-xs" aria-hidden="true"></i>
        <span>{{ t('home.settings') }}</span>
      </button>
      <router-link
        to="/admin"
        class="inline-flex items-center gap-2 px-3.5 py-2 rounded-lg bg-white border border-slate-300 text-slate-700 hover:text-blue-700 hover:border-blue-400 font-bold text-xs shadow-xs transition-colors"
        :title="t('home.adminTitle')"
      >
        <i class="fas fa-shield-halved text-blue-600 text-xs"></i>
        <span>{{ t('home.admin') }}</span>
      </router-link>
    </div>

    <div class="w-full max-w-[920px] flex flex-col items-center">
      
      <!-- Top Header -->
      <div class="text-center mb-8 md:mb-10 animate-in">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-slate-200 text-slate-800 font-bold text-xs mb-3 tracking-wider uppercase border border-slate-300">
          <span class="w-2 h-2 rounded-full bg-blue-600"></span>
          <span>{{ t('home.station') }}</span>
        </div>
        
        <h1 class="text-3xl md:text-4xl font-black tracking-tight text-slate-900 mb-2">
          {{ t('home.chooseStation') }}
        </h1>
        
        <p class="text-slate-600 font-medium text-xs md:text-sm max-w-md mx-auto">
          {{ t('home.chooseWorkflow') }}
        </p>
      </div>

      <!-- Customer Selection Cards Grid -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-5 w-full max-w-[820px]">
        
        <!-- Card 1: Khách hàng UI (item_scan) -->
        <div
          @click="selectCustomer('UI')"
          class="bg-white hover:bg-slate-50 border-2 border-slate-300 hover:border-blue-600 rounded-xl p-6 cursor-pointer transition-all shadow-xs hover:shadow-md flex flex-col justify-between min-h-[260px] group active:scale-98"
        >
          <div>
            <div class="flex items-center justify-between mb-4">
              <div class="w-12 h-12 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
                <i class="fas fa-barcode text-xl"></i>
              </div>
              <span class="px-2.5 py-1 text-xs font-black rounded-md bg-blue-100 text-blue-800 border border-blue-200 uppercase tracking-wider">
                {{ t('home.itemScan') }}
              </span>
            </div>

            <h2 class="text-xl font-black text-slate-900 mb-2 group-hover:text-blue-600 transition-colors">
              {{ uiCustomerName }}
            </h2>
            <p class="text-slate-600 text-xs leading-relaxed mb-4">
              {{ t('home.itemScanDescription') }}
            </p>
          </div>

          <div class="flex items-center justify-between text-blue-700 font-black text-xs pt-3 border-t border-slate-200">
            <span>{{ t('home.openPacking') }}</span>
            <i class="fas fa-arrow-right text-xs transition-transform group-hover:translate-x-1"></i>
          </div>
        </div>

        <!-- Card 2: Khách hàng Erro (weight_scale) -->
        <div
          @click="selectCustomer('ERRO')"
          class="bg-white hover:bg-slate-50 border-2 border-slate-300 hover:border-emerald-600 rounded-xl p-6 cursor-pointer transition-all shadow-xs hover:shadow-md flex flex-col justify-between min-h-[260px] group active:scale-98"
        >
          <div>
            <div class="flex items-center justify-between mb-4">
              <div class="w-12 h-12 rounded-lg bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600">
                <i class="fas fa-weight-scale text-xl"></i>
              </div>
              <span class="px-2.5 py-1 text-xs font-black rounded-md bg-emerald-100 text-emerald-800 border border-emerald-200 uppercase tracking-wider">
                {{ t('home.weightPacking') }}
              </span>
            </div>

            <h2 class="text-xl font-black text-slate-900 mb-2 group-hover:text-emerald-600 transition-colors">
              {{ erroCustomerName }}
            </h2>
            <p class="text-slate-600 text-xs leading-relaxed mb-4">
              {{ t('home.weightPackingDescription') }}
            </p>
          </div>

          <div class="flex items-center justify-between text-emerald-700 font-black text-xs pt-3 border-t border-slate-200">
            <span>{{ t('home.openWeightPacking') }}</span>
            <i class="fas fa-arrow-right text-xs transition-transform group-hover:translate-x-1"></i>
          </div>
        </div>
      </div>

    </div>

    <SettingsModal :show="showSettings" @close="showSettings = false" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import catalogApi from '../features/catalog/api';
import SettingsModal from '../features/settings/components/SettingsModal.vue';
import LanguageSwitch from '../core/components/LanguageSwitch.vue';
import type { Customer } from '../types/api';

const router = useRouter();
const { t } = useI18n();
const customers = ref<Customer[]>([]);
const loading = ref(true);
const showSettings = ref(false);

const fetchCustomers = async () => {
  try {
    const res = await catalogApi.getCustomers();
    customers.value = res.data;
  } catch (err) {
    console.error('Lỗi khi nạp danh sách khách hàng:', err);
  } finally {
    loading.value = false;
  }
};

const uiCustomerName = computed(() => {
  const c = customers.value.find(item => item.code.toUpperCase() === 'UI');
  return c ? c.name : t('home.uiFallbackName');
});

const erroCustomerName = computed(() => {
  const c = customers.value.find(item => item.code.toUpperCase() === 'ERRO');
  return c ? c.name : t('home.erroFallbackName');
});

const selectCustomer = (code: string) => {
  localStorage.setItem('selected_customer', code);
  if (code.toUpperCase() === 'ERRO') {
    router.push('/packing/erro');
  } else {
    router.push('/packing/ui');
  }
};

onMounted(() => {
  fetchCustomers();
});
</script>
