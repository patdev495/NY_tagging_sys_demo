<template>
  <div class="flex-1 flex flex-col justify-center items-center py-10 md:py-16">
    <div class="w-full max-w-[500px] bg-white border border-slate-300 rounded-xl p-6 md:p-8 shadow-md">
      <div class="text-center mb-6">
        <div class="w-14 h-14 bg-indigo-50 border border-indigo-200 rounded-xl flex items-center justify-center mx-auto mb-3 text-indigo-600">
          <i class="fas fa-barcode text-2xl"></i>
        </div>
        <h2 class="text-xl font-black text-slate-900 mb-1.5">{{ t('erro.job_order_title') }}</h2>
        <p class="text-slate-500 text-xs leading-relaxed max-w-sm mx-auto">
          {{ t('erro.job_order_description') }}
        </p>
      </div>

      <form class="space-y-4" @submit.prevent="resolve">
        <div>
          <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 pl-0.5">
            {{ t('erro.job_order_label') }}
          </label>
          <input
            ref="inputRef"
            v-model="value"
            type="text"
            autocomplete="off"
            autocorrect="off"
            spellcheck="false"
            :placeholder="t('erro.job_order_placeholder')"
            class="w-full h-14 border-2 rounded-xl px-4 text-xl outline-none bg-white font-barcode-mono font-black transition-all text-center tracking-wider shadow-xs uppercase"
            :class="error ? 'border-rose-500 text-rose-700 focus:border-rose-500 focus:ring-4 focus:ring-rose-500/15 bg-rose-50/20' : 'border-slate-300 focus:border-indigo-600 focus:ring-4 focus:ring-indigo-500/10 text-slate-900'"
            :disabled="isResolving"
          />
        </div>

        <div v-if="error" class="text-xs text-rose-700 bg-rose-50 p-3 rounded-lg border border-rose-200 font-medium flex items-start gap-2">
          <i class="fas fa-circle-exclamation text-rose-600 mt-0.5 shrink-0 text-sm"></i>
          <div>
            <strong class="block font-bold text-rose-800">{{ error }}</strong>
            <span class="text-[11px] text-rose-600 mt-0.5 block">{{ t('erro.job_order_error_hint') }}</span>
          </div>
        </div>

        <button
          type="submit"
          :disabled="!value.trim() || isResolving"
          class="w-full h-12 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-200 text-white disabled:text-slate-400 font-bold text-sm rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer shadow-xs active:scale-98"
        >
          <i v-if="isResolving" class="fas fa-spinner fa-spin"></i>
          <span v-else>{{ t('erro.confirm_job_order') }}</span>
          <span class="text-xs font-barcode-mono font-black px-1.5 py-0.5 bg-black/20 rounded">ENTER ↵</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import jobOrderApi from '../../../job_order/api';
import type { ErroJobOrderResolution } from '../../../../types/api';
import { userErrorMessage } from '../../../../i18n/errorMessage';

const { t } = useI18n();

const emit = defineEmits<{
  (e: 'resolved', resolution: ErroJobOrderResolution): void;
}>();

const inputRef = ref<HTMLInputElement | null>(null);
const value = ref('');
const error = ref('');
const isResolving = ref(false);

const focusInput = () => {
  inputRef.value?.focus();
  inputRef.value?.select();
};

const resolve = async () => {
  const jobOrder = value.value.trim();
  if (!jobOrder || isResolving.value) return;

  error.value = '';
  isResolving.value = true;
  try {
    const response = await jobOrderApi.resolveErroJobOrder(jobOrder);
    emit('resolved', response.data);
  } catch (err: unknown) {
    error.value = userErrorMessage(err, t);
    await nextTick();
    focusInput();
  } finally {
    isResolving.value = false;
  }
};

onMounted(focusInput);

defineExpose({ focusInput });
</script>
