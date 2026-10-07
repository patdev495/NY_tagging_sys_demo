<template>
  <div class="mb-3 animate-in" v-if="lastCarton">
    <!-- PRINTING state: slim pulsing bar -->
    <div
      v-if="lastCarton.status === 'PRINTING'"
      class="flex items-center gap-3 px-4 py-2.5 bg-blue-50 border border-blue-300 rounded-xl text-blue-900 text-sm font-bold"
    >
      <i class="fas fa-spinner fa-spin text-blue-600 text-base shrink-0"></i>
      <span class="flex-1">
        {{ t('print.printing_carton') }}:
        <span class="font-barcode-mono font-black text-blue-800 ml-1 tracking-wider">{{ lastCarton.carton_sn }}</span>
      </span>
      <span class="text-[11px] text-blue-500 font-normal font-mono animate-pulse">{{ t('print.sending_command') }}</span>
    </div>

    <!-- SUCCESS state: compact green banner -->
    <div
      v-else-if="lastCarton.status === 'SUCCESS'"
      class="flex items-center gap-3 px-4 py-2.5 bg-emerald-50 border border-emerald-300 rounded-xl"
    >
      <div class="w-7 h-7 rounded-md bg-emerald-600 text-white flex items-center justify-center shrink-0">
        <i class="fas fa-check text-xs"></i>
      </div>
      <div class="flex-1 min-w-0">
        <span class="text-xs font-bold text-emerald-700 uppercase tracking-wide block leading-none mb-0.5">
          {{ t('print.last_carton') }}
        </span>
        <span class="font-barcode-mono font-black text-emerald-900 text-base tracking-wider block truncate">
          {{ lastCarton.carton_sn }}
        </span>
      </div>
      <div class="flex items-center gap-2 shrink-0">
        <a
          :href="downloadUrl"
          class="px-3 py-1.5 bg-white border border-emerald-300 text-emerald-700 hover:bg-emerald-50 rounded-lg text-xs font-bold flex items-center gap-1.5 no-underline transition-colors cursor-pointer"
          download
          :title="t('print.download_btxml_title')"
        >
          <i class="fas fa-file-download text-[10px]"></i>
          {{ t('print.manual_download') }}
        </a>
        <button
          @click="$emit('retry')"
          class="px-3 py-1.5 bg-white border border-emerald-300 text-emerald-700 hover:bg-emerald-50 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-colors cursor-pointer active:scale-95"
          :title="t('print.reprint_this_title')"
        >
          <i class="fas fa-redo text-[10px]"></i>
          {{ t('print.reprint') }}
        </button>
      </div>
    </div>

    <!-- FAILED state: red urgent banner -->
    <div
      v-else
      class="flex items-center gap-3 px-4 py-2.5 bg-rose-50 border border-rose-400 border-l-4 border-l-rose-600 rounded-xl animate-shake"
    >
      <div class="w-7 h-7 rounded-md bg-rose-600 text-white flex items-center justify-center shrink-0">
        <i class="fas fa-exclamation text-xs"></i>
      </div>
      <div class="flex-1 min-w-0">
        <span class="text-xs font-bold text-rose-700 uppercase tracking-wide block leading-none mb-0.5">
          {{ t('print.attempt_failed') }}
        </span>
        <span class="font-barcode-mono font-black text-rose-900 text-base tracking-wider block truncate line-through opacity-70">
          {{ lastCarton.carton_sn }}
        </span>
        <span v-if="agentErrorMessage" class="text-[11px] text-rose-700 font-normal block mt-0.5 truncate">
          {{ agentErrorMessage }}
        </span>
      </div>
      <button
        @click="$emit('retry')"
        class="px-3 py-1.5 bg-rose-600 hover:bg-rose-700 text-white border border-rose-700 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-colors cursor-pointer shrink-0 active:scale-95"
      >
        <i class="fas fa-redo text-[10px]"></i>
        {{ t('print.try_again') }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';
import type { Carton } from '../../../types/api';

const { t } = useI18n();
const props = defineProps<{
  lastCarton: (Carton & { status?: string }) | null;
  agentErrorMessage: string;
}>();

defineEmits<{
  (e: 'retry'): void;
}>();

const downloadUrl = computed(() => {
  if (!props.lastCarton) return '';
  const base = import.meta.env.DEV
    ? `http://${window.location.hostname}:8001/api/v1`
    : '/api/v1';
  return `${base}/print/carton/${props.lastCarton.id}/btxml`;
});
</script>
