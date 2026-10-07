<template>
  <div
    v-if="show"
    class="fixed inset-0 bg-slate-900/80 flex justify-center items-center z-[2000] p-4"
    role="dialog"
    aria-modal="true"
  >
    <div
      class="w-full max-w-[560px] bg-white border rounded-2xl overflow-hidden shadow-2xl flex flex-col transition-all"
      :class="verificationError
        ? 'border-rose-500 ring-4 ring-rose-500/20 animate-shake'
        : 'border-slate-300'"
    >
      <!-- Header: Status indicator + title -->
      <div class="flex items-center gap-3 px-6 py-4 border-b border-slate-200 bg-slate-50">
        <div class="w-9 h-9 rounded-xl bg-blue-600 text-white flex items-center justify-center shrink-0">
          <i class="fas fa-barcode text-base"></i>
        </div>
        <div>
          <h2 class="font-black text-slate-900 text-lg leading-tight m-0">
            {{ t('packing.verification_title') }}
          </h2>
          <p class="text-xs text-slate-500 m-0 leading-tight mt-0.5">
            {{ t('packing.verification_hint') }}
          </p>
        </div>
        <!-- Scan ready indicator -->
        <div class="ml-auto flex items-center gap-1.5 text-emerald-700 text-xs font-bold">
          <span class="relative flex h-2 w-2">
            <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span class="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          {{ t('packing.ready') }}
        </div>
      </div>

      <!-- Body -->
      <div class="px-6 py-5 flex flex-col gap-4">

        <!-- Target SN: Large display -->
        <div>
          <span class="text-[11px] font-bold text-slate-400 uppercase tracking-widest block mb-2">
            {{ t('packing.expected_sn') }}
          </span>
          <div class="bg-slate-900 border border-slate-700 rounded-xl p-4 text-center">
            <span class="font-barcode-mono font-black text-white text-2xl md:text-3xl tracking-widest select-all">
              {{ carton?.carton_sn }}
            </span>
          </div>
        </div>

        <!-- Product info grid -->
        <div class="grid grid-cols-3 gap-2">
          <div class="bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block leading-none mb-1">{{ t('packing.product_label') }}</span>
            <span class="text-slate-800 font-semibold text-xs block truncate" :title="currentProduct?.item_name">
              {{ currentProduct?.item_name || 'N/A' }}
            </span>
          </div>
          <div class="bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block leading-none mb-1">Work Order</span>
            <span class="text-slate-800 font-barcode-mono font-bold text-xs block">{{ carton?.job_order || 'N/A' }}</span>
          </div>
          <div class="bg-slate-50 border border-slate-200 rounded-lg px-3 py-2">
            <span class="text-[10px] font-bold text-slate-400 uppercase tracking-wider block leading-none mb-1">{{ t('packing.items_label') }}</span>
            <span class="text-slate-800 font-barcode-mono font-bold text-sm block">{{ carton?.items?.length || scannedCount }} pcs</span>
          </div>
        </div>

        <!-- Scan Input Field -->
        <div class="relative">
          <div
            class="flex items-center gap-3 border-2 rounded-xl px-4 py-3 bg-white transition-all duration-200"
            :class="verificationError
              ? 'border-rose-500 bg-rose-50'
              : 'border-slate-300 focus-within:border-blue-500 focus-within:ring-4 focus-within:ring-blue-500/10 focus-within:bg-white'"
          >
            <i
              class="fas fa-barcode text-xl shrink-0 transition-colors"
              :class="verificationError ? 'text-rose-500' : 'text-slate-400'"
            ></i>
            <input
              ref="verificationInputRef"
              v-model="verificationScanBuffer"
              @keydown.enter.prevent="handleScan"
              :placeholder="t('packing.verification_placeholder')"
              class="flex-1 border-none outline-none bg-transparent text-base font-barcode-mono font-bold text-slate-900 placeholder:text-slate-400 placeholder:font-normal"
              autocomplete="off"
              spellcheck="false"
            />
            <span
              v-if="verificationScanBuffer"
              class="text-xs font-bold px-2 py-1 bg-blue-600 text-white rounded-md cursor-pointer"
              @click="handleScan"
              :title="t('packing.confirm_enter')"
            >Enter</span>
          </div>

          <!-- Error inline -->
          <div
            v-if="verificationError"
            class="mt-2 flex items-center gap-2 text-rose-600 text-sm font-bold"
          >
            <i class="fas fa-exclamation-circle text-base"></i>
            <span>{{ t('packing.verification_error') }}</span>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div class="px-6 py-4 bg-slate-50 border-t border-slate-200 flex justify-between items-center gap-3">
        <button
          @click="$emit('resetSession')"
          class="px-4 py-2 bg-white border border-slate-300 text-slate-600 hover:text-slate-900 hover:bg-slate-100 rounded-xl text-sm font-bold cursor-pointer transition-all flex items-center gap-2 active:scale-95"
        >
          <i class="fas fa-home text-slate-500 text-xs"></i>
          <span>{{ t('packing.back_home') }}</span>
        </button>

        <div class="flex items-center gap-1.5 text-slate-400 text-xs">
          <i class="fas fa-keyboard animate-pulse"></i>
          <span>{{ t('packing.waiting_scanner') }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Carton, Product } from '../../../types/api';

const props = defineProps<{
  show: boolean;
  carton: (Carton & { status?: string, items?: { item_sn: string }[] }) | null;
  currentProduct: Product | null;
  scannedCount?: number;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'verified', carton: Carton): void;
  (e: 'resetSession'): void;
  (e: 'scanAlert'): void;
}>();

const { t } = useI18n();
const verificationScanBuffer = ref<string>('');
const verificationInputRef = ref<HTMLInputElement | null>(null);
const verificationError = ref<boolean>(false);

const focusInput = () => {
  nextTick(() => {
    if (verificationInputRef.value) {
      verificationInputRef.value.focus();
    }
  });
};

watch(() => props.show, (newVal) => {
  if (newVal) {
    verificationScanBuffer.value = '';
    verificationError.value = false;
    focusInput();
  }
});

const handleScan = () => {
  const scannedVal = verificationScanBuffer.value.trim();
  if (!scannedVal || !props.carton) return;

  const expectedVal = props.carton.carton_sn.trim();
  if (scannedVal.toLowerCase() === expectedVal.toLowerCase()) {
    verificationError.value = false;
    emit('verified', props.carton);
  } else {
    emit('scanAlert');
    verificationError.value = true;
    verificationScanBuffer.value = '';
    setTimeout(() => {
      verificationError.value = false;
    }, 1500);
  }
};

defineExpose({
  focusInput,
});
</script>
