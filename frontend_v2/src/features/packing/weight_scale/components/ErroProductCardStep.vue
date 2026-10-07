<template>
  <div class="flex-1 flex flex-col justify-center items-center py-2 px-2 overflow-y-auto min-h-0 w-full animate-in">
    <div class="w-full max-w-[960px] space-y-2.5 my-auto">
      <!-- Breadcrumb / Job Order Bar -->
      <div class="flex justify-between items-center px-1">
        <span class="text-xs text-slate-600 font-bold uppercase tracking-wider">
          {{ t('erro.job_order_label') }}: <strong class="font-barcode-mono text-indigo-900 text-sm">{{ jobOrder }}</strong>
          <span v-if="resolution?.factory_part_number" class="text-slate-500 font-normal ml-1">
            ({{ resolution.factory_part_number }})
          </span>
        </span>
        <div class="flex items-center gap-2">
          <button 
            type="button"
            @click="$emit('changeJobOrder')" 
            class="text-indigo-600 hover:text-indigo-800 border-none bg-transparent font-bold cursor-pointer text-xs flex items-center gap-1.5 hover:underline"
          >
            <i class="fas fa-arrow-rotate-left"></i> {{ t('erro.change_job_order') }}
          </button>
          <LanguageSwitch variant="header" />
        </div>
      </div>

      <!-- 2-Column Grid on md+ screens -->
      <div class="grid grid-cols-1 md:grid-cols-12 gap-3 items-stretch">
        <!-- Left: Main Product Confirmation Card (7 cols) -->
        <div 
          v-if="resolution"
          class="md:col-span-7 bg-slate-900 text-white rounded-xl p-4 shadow-lg border border-slate-800 flex flex-col justify-between"
        >
          <div>
            <div class="flex justify-between items-start mb-2">
              <div class="flex items-center gap-2">
                <span class="bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded-md px-2 py-0.5 text-xs font-bold uppercase tracking-wider">
                  {{ t('erro.confirm_erro_product') }}
                </span>
                <span class="bg-slate-800 text-slate-300 border border-slate-700 rounded-md px-2 py-0.5 text-[11px] font-mono font-bold uppercase">
                  {{ resolution.product.template_type }}
                </span>
              </div>
              <span class="text-xs font-mono text-slate-400">
                Factory P/N: <strong class="text-white font-barcode-mono">{{ resolution.factory_part_number }}</strong>
              </span>
            </div>

            <!-- Product Item Name -->
            <h3 class="text-lg font-black leading-tight mb-0.5 tracking-wide text-white">
              {{ resolution.product.item_name }}
            </h3>
            <p class="text-xs text-slate-400 mb-2 font-mono">
              {{ t('erro.erp_item_name') }}: <span class="text-slate-300">{{ resolution.customer_ref }}</span>
            </p>

            <!-- Warning if name mismatch -->
            <div 
              v-if="resolution.name_mismatch" 
              class="text-xs bg-amber-500/10 border border-amber-500/30 text-amber-300 p-2 rounded-lg mb-2 flex items-start gap-2"
            >
              <i class="fas fa-triangle-exclamation text-amber-400 mt-0.5 shrink-0 text-sm"></i>
              <div>
                <strong class="block font-bold">{{ t('erro.name_mismatch_warning_title') }}</strong>
                <span class="text-[11px] text-amber-200/80 block mt-0.5">
                  {{ t('erro.name_mismatch_warning_desc', { ref: resolution.customer_ref }) }}
                </span>
              </div>
            </div>
          </div>

          <!-- Key Metrics 3-Column Grid -->
          <div class="grid grid-cols-3 gap-2 border-t border-slate-800/80 pt-3 text-center mt-auto">
            <div class="bg-slate-800/60 rounded-lg p-2 border border-slate-700/60">
              <span class="text-slate-400 text-[10px] uppercase font-bold block mb-0.5">{{ t('packing.specification') }}</span>
              <span class="text-base font-black text-white font-barcode-mono">
                {{ resolution.product.packed_qty }} <span class="text-[10px] font-normal text-slate-400">{{ t('packing.pcs_per_carton') }}</span>
              </span>
            </div>

            <div class="bg-slate-800/60 rounded-lg p-2 border border-slate-700/60">
              <span class="text-slate-400 text-[10px] uppercase font-bold block mb-0.5">{{ t('erro.production_quantity') }}</span>
              <span class="text-base font-black text-emerald-400 font-barcode-mono">
                {{ resolution.total_qty.toLocaleString() }} <span class="text-[10px] font-normal text-slate-400">PCS</span>
              </span>
            </div>

            <div class="bg-slate-800/60 rounded-lg p-2 border border-slate-700/60">
              <span class="text-slate-400 text-[10px] uppercase font-bold block mb-0.5">{{ t('erro.planned_packing') }}</span>
              <span class="text-base font-black text-indigo-400 font-barcode-mono">
                {{ resolution.planned_cartons }} <span class="text-[10px] font-normal text-slate-400">{{ t('packing.cartons_unit') }}</span>
              </span>
            </div>
          </div>
        </div>

        <!-- Right: PO & LOT Form Box + Prominent Action Button (5 cols) -->
        <div class="md:col-span-5 flex flex-col justify-between">
          <form @submit.prevent="handleSubmit" class="h-full flex flex-col justify-between gap-3">
            <div class="bg-white border border-slate-200 rounded-xl p-3.5 shadow-xs space-y-2.5 flex-1 flex flex-col justify-center">
              <div class="flex items-center gap-2 pb-1.5 border-b border-slate-100 text-xs font-bold text-slate-700 uppercase tracking-wider">
                <i class="fas fa-tags text-indigo-600"></i>
                <span>{{ t('erro.po_lot_config_title') }}</span>
              </div>

              <template v-if="resolution?.product.template_type !== 'erro_02'">
                <div class="space-y-2">
                  <div>
                    <label for="batch-po" class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                      {{ t('erro.po_number') }} {{ isPoRequired ? '*' : `(${t('common.optional')})` }}
                    </label>
                    <input
                      id="batch-po"
                      ref="poInputRef"
                      v-model="formPo"
                      type="text"
                      :required="isPoRequired"
                      :placeholder="isPoRequired ? t('erro.po_required_placeholder') : t('erro.po_optional_placeholder')"
                      class="w-full px-3 py-1.5 rounded-lg border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-sm font-mono"
                    />
                  </div>

                  <div>
                    <label for="batch-lot" class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                      {{ t('erro.lot_number') }} ({{ t('erro.auto') }})
                    </label>
                    <input
                      id="batch-lot"
                      type="text"
                      disabled
                      :value="formLot"
                      :placeholder="t('erro.lot_auto_placeholder')"
                      class="w-full px-3 py-1.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-500 outline-none text-sm font-mono cursor-not-allowed"
                    />
                  </div>
                </div>
              </template>
              <div v-else class="text-xs text-slate-500 italic bg-slate-50 p-3 rounded-lg border border-slate-200 text-center my-auto">
                {{ t('erro.not_applicable_template_2') }}
              </div>
            </div>

            <!-- Prominent Primary Call-to-Action Button -->
            <button
              type="submit"
              class="w-full h-13 bg-emerald-600 hover:bg-emerald-700 text-white font-black text-base rounded-xl transition-all shadow-md flex items-center justify-center gap-2.5 cursor-pointer active:scale-98 shrink-0"
              :title="t('erro.start_weighing')"
            >
              <i class="fas fa-play text-sm"></i>
              <span>{{ t('erro.start_weighing') }}</span>
              <span class="text-xs font-barcode-mono font-black px-2 py-0.5 bg-black/25 rounded tracking-wider">ENTER ↵</span>
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import { useI18n } from 'vue-i18n';
import type { ErroJobOrderResolution } from '../../../../types/api';
import LanguageSwitch from '../../../../core/components/LanguageSwitch.vue';

const { t } = useI18n();

const props = defineProps<{
  jobOrder: string;
  resolution: ErroJobOrderResolution | null;
  initialPo?: string;
  initialLot?: string;
}>();

const emit = defineEmits<{
  (e: 'changeJobOrder'): void;
  (e: 'confirm', payload: { po: string; lot: string }): void;
}>();

const poInputRef = ref<HTMLInputElement | null>(null);
const formPo = ref(props.initialPo || '');
const formLot = ref(props.initialLot || '');

const automaticLot = () => {
  const now = new Date();
  return `${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}`;
};

const templateType = computed(() => props.resolution?.product.template_type);

const isPoRequired = computed(() => {
  return templateType.value === 'erro_01' || templateType.value === 'erro_04';
});

const initDefaults = () => {
  if (!props.resolution) return;
  formPo.value = props.initialPo || '';

  formLot.value = props.initialLot || automaticLot();
};

watch(() => props.resolution, initDefaults, { immediate: true });

const handleSubmit = () => {
  if (isPoRequired.value && !formPo.value.trim()) {
    poInputRef.value?.focus();
    return;
  }
  emit('confirm', {
    po: formPo.value.trim(),
    lot: formLot.value.trim(),
  });
};

const handleKeyDown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' && !['TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) {
    e.preventDefault();
    handleSubmit();
  }
};

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown);
  if (isPoRequired.value && !formPo.value) {
    poInputRef.value?.focus();
  }
});

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown);
});
</script>
