<template>
  <div class="flex-1 flex flex-col justify-center items-center py-10 md:py-16">
    <div class="w-full max-w-[500px] bg-white border border-slate-300 rounded-xl p-6 md:p-8 shadow-md">
      <div class="text-center mb-6">
        <div class="w-14 h-14 bg-blue-50 border border-blue-200 rounded-xl flex items-center justify-center mx-auto mb-3 text-blue-600">
          <i class="fas fa-barcode text-2xl"></i>
        </div>
        <h2 class="text-xl font-black text-slate-900 mb-1.5">{{ t('packing.enter_job_order_title') }}</h2>
        <p class="text-slate-500 text-xs leading-relaxed max-w-sm mx-auto">
          {{ t('packing.enter_job_order_desc') }}
        </p>
      </div>

      <form @submit.prevent="handleSubmit" class="space-y-4">
        <div>
          <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5 pl-0.5">
            {{ t('packing.job_order_label') }}
          </label>
          <div class="relative">
            <input
              ref="inputRef"
              :value="modelValue"
              @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
              :placeholder="t('packing.job_order_placeholder')"
              class="w-full h-14 border-2 rounded-xl px-4 text-xl outline-none bg-white font-barcode-mono font-black transition-all text-center tracking-wider shadow-xs"
              :class="hasError
                ? 'border-rose-500 text-rose-700 focus:border-rose-500 focus:ring-4 focus:ring-rose-500/15 bg-rose-50/20'
                : 'border-slate-300 focus:border-blue-600 focus:ring-4 focus:ring-blue-500/10 text-slate-900'"
              autocomplete="off"
              autocorrect="off"
              spellcheck="false"
              :disabled="isLoading"
            />
          </div>
        </div>

        <!-- Job Order Error Alert with recovery instructions -->
        <div 
          v-if="hasError && errorText"
          class="text-xs text-rose-700 bg-rose-50 p-3 rounded-lg border border-rose-200 font-medium flex items-start gap-2 animate-in"
        >
          <i class="fas fa-circle-exclamation text-rose-600 mt-0.5 shrink-0 text-sm"></i>
          <div>
            <strong class="block font-bold text-rose-800">{{ errorText }}</strong>
            <span class="text-[11px] text-rose-600 mt-0.5 block">{{ t('packing.job_order_recovery') }}</span>
          </div>
        </div>

        <button
          type="submit"
          :disabled="!modelValue.trim() || isLoading"
          class="w-full h-12 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-200 text-white disabled:text-slate-400 font-bold text-sm rounded-xl transition-all flex items-center justify-center gap-2 cursor-pointer shadow-xs active:scale-98"
        >
          <i v-if="isLoading" class="fas fa-spinner fa-spin"></i>
          <span v-else>{{ t('packing.confirm') }}</span>
          <span class="text-xs font-barcode-mono font-black px-1.5 py-0.5 bg-black/20 rounded">ENTER ↵</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';

defineProps<{
  modelValue: string;
  isLoading?: boolean;
  hasError?: boolean;
  errorText?: string;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
  (e: 'submit'): void;
}>();

const { t } = useI18n();
const inputRef = ref<HTMLInputElement | null>(null);

const handleSubmit = () => {
  emit('submit');
};

const focusInput = () => {
  if (inputRef.value) {
    inputRef.value.focus();
    inputRef.value.select();
  }
};

onMounted(() => {
  focusInput();
});

defineExpose({
  focusInput,
});
</script>
