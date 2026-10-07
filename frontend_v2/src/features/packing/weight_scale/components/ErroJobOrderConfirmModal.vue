<template>
  <div 
    v-if="show && resolution" 
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in"
  >
    <div class="bg-white rounded-3xl shadow-2xl max-w-lg w-full p-6 border border-slate-100 flex flex-col gap-5">
      <div class="flex items-center justify-between pb-3 border-b border-slate-100">
        <div class="flex items-center gap-2.5">
          <div class="w-9 h-9 rounded-xl bg-indigo-50 border border-indigo-200 flex items-center justify-center text-indigo-600">
            <i class="fas fa-clipboard-check text-base"></i>
          </div>
          <div>
            <h2 class="font-black text-base md:text-lg text-slate-900 leading-tight">{{ t('erro.confirm_job_order_title') }}</h2>
            <p class="text-[11px] text-slate-500 leading-none">{{ t('erro.reconcile_erp_desc') }}</p>
          </div>
        </div>
        <button @click="$emit('close')" class="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg cursor-pointer">
          <i class="fas fa-times text-lg"></i>
        </button>
      </div>

      <!-- Overview Info Cards -->
      <div class="bg-slate-50 border border-slate-200/80 rounded-2xl p-4 grid grid-cols-2 gap-3 text-xs">
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">{{ t('erro.job_order_label') }}:</span>
          <span class="font-mono font-black text-sm text-indigo-900">{{ resolution.job_order }}</span>
        </div>
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">Factory P/N:</span>
          <span class="font-mono font-bold text-sm text-slate-800">{{ resolution.factory_part_number }}</span>
        </div>
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">{{ t('erro.erp_item_name') }}:</span>
          <span class="font-bold text-slate-800 break-words">{{ resolution.customer_ref }}</span>
        </div>
        <div>
          <span class="text-[10px] uppercase font-bold text-slate-400 block tracking-wider">{{ t('erro.system_product') }}:</span>
          <div class="flex items-center gap-1.5 flex-wrap">
            <span class="font-bold text-slate-900">{{ resolution.product.item_name }}</span>
            <span class="px-1.5 py-0.5 rounded text-[10px] font-black bg-indigo-100 text-indigo-700 uppercase">
              {{ resolution.product.template_type }}
            </span>
          </div>
        </div>
        <div class="col-span-2 pt-2 border-t border-slate-200/60 flex items-center justify-between">
          <div>
            <span class="text-[10px] uppercase font-bold text-slate-400 block">{{ t('erro.production_quantity') }}:</span>
            <span class="font-bold text-slate-800">{{ resolution.total_qty.toLocaleString() }} PCS</span>
          </div>
          <div class="text-right">
            <span class="text-[10px] uppercase font-bold text-slate-400 block">{{ t('erro.planned_packing') }}:</span>
            <span class="font-black text-indigo-700">{{ resolution.planned_cartons }} {{ t('packing.carton') }} ({{ resolution.product.packed_qty }} {{ t('packing.pcs_per_carton') }})</span>
          </div>
        </div>
      </div>

      <!-- Warning if name mismatch -->
      <div 
        v-if="resolution.name_mismatch" 
        class="text-xs bg-amber-50 border border-amber-300 text-amber-900 p-3 rounded-xl flex items-start gap-2"
      >
        <i class="fas fa-triangle-exclamation text-amber-600 mt-0.5 shrink-0 text-sm"></i>
        <div>
          <strong class="block font-bold">{{ t('erro.name_mismatch_warning_title') }}</strong>
          <span class="text-[11px] text-amber-700 block mt-0.5">
            {{ t('erro.name_mismatch_warning_desc', { ref: resolution.customer_ref }) }}
          </span>
        </div>
      </div>

      <!-- PO & LOT Inputs -->
      <form @submit.prevent="handleConfirm" class="space-y-3.5">
        <template v-if="resolution.product.template_type !== 'erro_02'">
          <div>
            <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              {{ t('erro.po_number') }} {{ isPoRequired ? '*' : `(${t('common.optional')})` }}
            </label>
            <input
              v-model="formPo"
              type="text"
              :required="isPoRequired"
              :placeholder="isPoRequired ? t('erro.po_required_placeholder') : t('erro.po_optional_placeholder')"
              class="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none text-sm font-mono"
            />
          </div>

          <div>
            <label class="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
              {{ t('erro.lot_number') }} ({{ t('erro.auto') }})
            </label>
            <input
              type="text"
              disabled
              :value="formLot"
              :placeholder="t('erro.lot_auto_placeholder')"
              class="w-full px-3.5 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-slate-500 outline-none text-sm font-mono cursor-not-allowed"
            />
          </div>
        </template>
        <div v-else class="text-xs text-slate-500 italic bg-slate-50 p-2.5 rounded-lg border border-slate-200">
          {{ t('erro.not_applicable_template_2') }}
        </div>

        <div class="flex justify-end gap-2.5 pt-3">
          <button
            type="button"
            @click="$emit('close')"
            class="px-4 py-2.5 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs transition-all cursor-pointer"
          >
            {{ t('erro.cancel_rescan') }}
          </button>
          <button
            type="submit"
            class="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs transition-all cursor-pointer shadow-md shadow-indigo-600/20 flex items-center gap-1.5"
          >
            <span>{{ t('erro.start_weighing') }}</span>
            <span class="text-[10px] font-barcode-mono font-black px-1.5 py-0.5 bg-black/20 rounded">ENTER ↵</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import type { ErroJobOrderResolution } from '../../../../types/api';

const { t } = useI18n();

const props = defineProps<{
  show: boolean;
  resolution: ErroJobOrderResolution | null;
  initialPo?: string;
  initialLot?: string;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'confirm', payload: { po: string; lot: string }): void;
}>();

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

watch(
  () => props.show,
  (isShown) => {
    if (isShown && props.resolution) {
      formPo.value = props.initialPo || '';
      
      formLot.value = props.initialLot || automaticLot();
    }
  }
);

const handleConfirm = () => {
  if (isPoRequired.value && !formPo.value.trim()) return;
  emit('confirm', {
    po: formPo.value.trim(),
    lot: formLot.value.trim(),
  });
};
</script>
