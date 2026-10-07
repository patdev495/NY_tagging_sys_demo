<template>
  <nav aria-label="Workflow Steps" class="flex items-center justify-between px-3.5 py-2 my-2 bg-slate-50 border border-slate-200 rounded-lg text-xs shrink-0">
    <div class="flex items-center gap-2">
      <span class="font-bold text-slate-500 uppercase tracking-wider text-[11px]">{{ t('erro.workflow') }}</span>
      <div class="flex items-center gap-1.5 font-bold">
        <span :class="currentStep === 1 ? 'px-2.5 py-1 rounded bg-indigo-600 text-white shadow-xs' : 'px-2 py-0.5 rounded bg-slate-200 text-slate-600'">
          {{ t('erro.step_job_order') }}
        </span>
        <i class="fas fa-chevron-right text-[10px] text-slate-400"></i>
        <span :class="currentStep === 2 ? 'px-2.5 py-1 rounded bg-indigo-600 text-white shadow-xs' : (currentStep > 2 ? 'px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-200' : 'px-2 py-0.5 rounded bg-slate-100 text-slate-400')">
          {{ t('erro.step_confirm_order') }}
        </span>
        <i class="fas fa-chevron-right text-[10px] text-slate-400"></i>
        <span :class="currentStep === 3 ? 'px-2.5 py-1 rounded bg-emerald-600 text-white shadow-xs' : 'px-2 py-0.5 rounded bg-slate-100 text-slate-400'">
          {{ t('erro.step_weigh_pack') }}
        </span>
      </div>
    </div>

    <div v-if="jobOrder" class="flex items-center gap-2 md:gap-3 font-mono text-xs">
      <span class="text-slate-600">{{ t('erro.work_order') }} <strong class="text-slate-900 font-barcode-mono font-bold">{{ jobOrder }}</strong></span>
      <span v-if="factoryPartNumber" class="text-slate-500 hidden md:inline">({{ factoryPartNumber }})</span>
      <span v-if="productItemName" class="text-slate-600 hidden sm:inline">| {{ t('erro.product_abbr') }} <strong class="text-slate-900">{{ productItemName }}</strong></span>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

defineProps<{
  currentStep: 1 | 2 | 3;
  jobOrder?: string;
  factoryPartNumber?: string;
  productItemName?: string;
}>();
</script>
