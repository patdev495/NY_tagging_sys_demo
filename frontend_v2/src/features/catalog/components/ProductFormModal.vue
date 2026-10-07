<template>
  <div v-if="show" class="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs overflow-y-auto">
    <div class="bg-white rounded-3xl shadow-2xl w-full max-w-3xl overflow-hidden animate-in fade-in zoom-in duration-200 my-8 border border-slate-100">

      <!-- Modal Header -->
      <div class="p-6 bg-slate-900 text-white flex justify-between items-center">
        <div class="flex items-center gap-3">
          <div class="w-10 h-10 rounded-xl bg-indigo-600 flex items-center justify-center font-bold text-lg">
            <i class="fas fa-box"></i>
          </div>
          <div>
            <h2 class="text-xl font-bold tracking-tight">{{ isEdit ? t('products.modal_edit_title') : t('products.modal_create_title') }}</h2>
            <p class="text-xs text-slate-400 mt-0.5">{{ t('products.modal_subtitle') }}</p>
          </div>
        </div>
        <button @click="$emit('close')" class="text-slate-400 hover:text-white p-2 rounded-xl hover:bg-slate-800 transition-colors cursor-pointer">
          <X class="w-6 h-6" />
        </button>
      </div>

      <form @submit.prevent="handleSubmit" class="p-6 space-y-6 max-h-[80vh] overflow-y-auto">

        <!-- SECTION 1: Basic Info -->
        <div class="space-y-4">
          <div class="flex items-center gap-2 pb-2 border-b border-slate-100 text-slate-900 font-bold text-sm">
            <i class="fas fa-info-circle text-indigo-600"></i>
            <span>{{ t('products.sec_basic_info') }}</span>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-1.5">
              <label class="text-xs font-bold text-slate-700 uppercase">{{ t('products.customer_label') }}</label>
              <select v-model="formData.customer_id" @change="onCustomerChange" required class="w-full p-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none bg-white font-medium text-sm">
                <option v-for="c in customers" :key="c.id" :value="c.id">{{ c.name }} ({{ c.code }})</option>
              </select>
            </div>
            <div class="space-y-1.5">
              <label class="text-xs font-bold text-slate-700 uppercase">{{ t('products.product_name_label') }}</label>
              <input v-model="formData.item_name" type="text" required placeholder="e.g. 840-00083 or UVC-G4-PRO" class="w-full p-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none font-mono text-sm font-bold">
            </div>
          </div>
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div class="space-y-1.5">
              <label class="text-xs font-bold text-slate-700 uppercase">{{ t('products.packed_qty_label') }}</label>
              <input v-model.number="formData.packed_qty" type="number" required min="1" class="w-full p-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none font-mono text-sm font-bold">
            </div>
            <div class="space-y-1.5">
              <label class="text-xs font-bold text-slate-700 uppercase">{{ t('products.template_label') }}</label>
              <!-- Erro: fixed canonical template -->
              <div v-if="isErroProduct" class="w-full flex items-center gap-2 p-3 rounded-xl border border-purple-200 bg-purple-50/60 text-xs font-mono text-purple-900">
                <span class="px-2 py-0.5 rounded bg-purple-200 text-purple-800 font-bold uppercase text-[10px] shrink-0">{{ t('products.fixed_erro_template') }}</span>
                <span class="font-bold flex-1 truncate">📄 {{ erroTemplateName }}</span>
                <span class="text-[11px] text-purple-600 font-sans hidden sm:inline shrink-0">({{ erroTemplateLabel }})</span>
              </div>
              <!-- UI products: select template -->
              <div v-else class="space-y-1">
                <select v-model="formData.template_path" class="w-full p-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none bg-white font-mono text-xs font-bold text-slate-800">
                  <option v-if="formData.template_path && !UI_TEMPLATES.some(t => t.filename === formData.template_path)" :value="formData.template_path">
                    📄 {{ formData.template_path }} ({{ t('products.current_in_db') }})
                  </option>
                  <option v-for="tmpl in UI_TEMPLATES" :key="tmpl.filename" :value="tmpl.filename">📄 {{ tmpl.label }}</option>
                </select>
                <p class="text-[10px] text-slate-400">{{ t('products.template_ui_hint') }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- SECTION 2: Packing Mode -->
        <div class="space-y-4 pt-2">
          <div class="flex items-center gap-2 pb-2 border-b border-slate-100 text-slate-900 font-bold text-sm">
            <i class="fas fa-sliders text-indigo-600"></i>
            <span>{{ t('products.sec_packing_mode') }}</span>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div @click="setPackingMode('item_scan')" :class="['p-4 rounded-2xl border-2 cursor-pointer transition-all flex items-start gap-3', formData.packing_mode === 'item_scan' ? 'border-indigo-600 bg-indigo-50/50 shadow-xs' : 'border-slate-200 hover:border-slate-300 bg-white']">
              <div :class="['w-8 h-8 rounded-lg flex items-center justify-center shrink-0 font-bold', formData.packing_mode === 'item_scan' ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-600']"><i class="fas fa-barcode"></i></div>
              <div>
                <div class="font-bold text-sm text-slate-900">{{ t('products.item_scan_mode_title') }}</div>
                <p class="text-xs text-slate-500 mt-0.5">{{ t('products.item_scan_mode_desc') }}</p>
              </div>
            </div>
            <div @click="setPackingMode('weight_scale')" :class="['p-4 rounded-2xl border-2 cursor-pointer transition-all flex items-start gap-3', formData.packing_mode === 'weight_scale' ? 'border-emerald-600 bg-emerald-50/50 shadow-xs' : 'border-slate-200 hover:border-slate-300 bg-white']">
              <div :class="['w-8 h-8 rounded-lg flex items-center justify-center shrink-0 font-bold', formData.packing_mode === 'weight_scale' ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-600']"><i class="fas fa-weight-scale"></i></div>
              <div>
                <div class="font-bold text-sm text-slate-900">{{ t('products.weight_scale_mode_title') }}</div>
                <p class="text-xs text-slate-500 mt-0.5">{{ t('products.weight_scale_mode_desc') }}</p>
              </div>
            </div>
          </div>
          <!-- Item Scan extras -->
          <div v-if="formData.packing_mode === 'item_scan'" class="p-4 bg-slate-50 rounded-2xl border border-slate-200 space-y-3">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-1">
                <label class="text-xs font-bold text-slate-700 uppercase">{{ t('products.upc_label') }}</label>
                <input v-model="formData.upc" type="text" :placeholder="t('products.upc_placeholder')" class="w-full p-2.5 rounded-xl border border-slate-200 bg-white focus:ring-2 focus:ring-indigo-500 outline-none font-mono text-xs">
              </div>
              <div class="flex items-center pt-5">
                <label class="flex items-center gap-2.5 cursor-pointer select-none">
                  <input v-model="formData.allow_partial" type="checkbox" :true-value="1" :false-value="0" class="w-4 h-4 rounded text-indigo-600 focus:ring-indigo-500 cursor-pointer">
                  <span class="text-xs font-bold text-slate-700">{{ t('products.allow_partial_label') }}</span>
                </label>
              </div>
            </div>
          </div>
          <!-- Weight Scale tolerance -->
          <div v-if="formData.packing_mode === 'weight_scale'" class="p-4 bg-emerald-50/60 rounded-2xl border border-emerald-200 space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold uppercase text-emerald-900 flex items-center gap-1.5">
                <i class="fas fa-shield-halved text-emerald-600"></i>
                <span>{{ t('products.weight_tolerance_title') }}</span>
              </span>
              <span class="text-[10px] text-emerald-700 font-semibold bg-emerald-100 px-2 py-0.5 rounded">{{ t('products.weight_unit_kg') }}</span>
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div class="space-y-1.5">
                <label class="text-xs font-bold text-slate-700 uppercase">{{ t('products.min_weight') }}</label>
                <input v-model.number="formData.min_weight" type="number" step="0.001" required placeholder="12.300" class="w-full p-3 rounded-xl border border-emerald-300 bg-white focus:ring-2 focus:ring-emerald-500 outline-none font-mono font-bold text-sm text-slate-900" />
              </div>
              <div class="space-y-1.5">
                <label class="text-xs font-bold text-slate-700 uppercase">{{ t('products.max_weight') }}</label>
                <input v-model.number="formData.max_weight" type="number" step="0.001" required placeholder="12.700" class="w-full p-3 rounded-xl border border-emerald-300 bg-white focus:ring-2 focus:ring-emerald-500 outline-none font-mono font-bold text-sm text-slate-900" />
              </div>
            </div>
          </div>
        </div>

        <!-- SECTION 3: Label & S/N Specs -->
        <div class="space-y-4 pt-2">
          <div class="flex items-center gap-2 pb-2 border-b border-slate-100 text-slate-900 font-bold text-sm">
            <i class="fas fa-tag text-indigo-600"></i>
            <span>{{ t('products.sec_template_fields') }}</span>
          </div>
          <div class="space-y-1.5">
            <label class="text-xs font-bold text-slate-700 uppercase">{{ t('products.template_type_label') }}</label>
            <select v-model="formData.template_type" @change="onTemplateTypeChange" class="w-full p-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-indigo-500 outline-none bg-white font-medium text-sm">
              <optgroup label="Khách Hàng Erro">
                <option value="erro_05">Erro 05 (Pegatron NN9 PD016906 — erro_05.btw)</option>
                <option value="erro_04">Erro 04 (eero PD027032 — erro_04.btw)</option>
                <option value="erro_03">Erro 03 (Luxshare NME PD024364 — erro_03.btw)</option>
                <option value="erro_02">Erro 02 (PD027504 Pallet SSCC + ASIN — erro_02.btw)</option>
                <option value="erro_01">Erro 01 (PD014736 Carton SN + Rev — erro_01.btw)</option>
              </optgroup>
              <optgroup label="Khách Hàng UI">
                <option value="standard">Standard (Tem thùng cơ bản)</option>
                <option value="detailed">Detailed (Lưới 40 mã sê-ri con)</option>
              </optgroup>
            </select>
          </div>

          <!-- Factory P/N Mapping for Erro templates -->
          <div v-if="isErroProduct" class="p-4 bg-indigo-50/60 rounded-2xl border border-indigo-200 space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold uppercase text-indigo-900 flex items-center gap-1.5">
                <i class="fas fa-barcode text-indigo-600"></i>
                <span>{{ t('products.factory_pn_title') }}</span>
              </span>
              <span v-if="isEdit && initialData?.id" class="text-[10px] text-indigo-700 font-semibold bg-indigo-100 px-2 py-0.5 rounded">
                {{ t('products.mappings_count', { count: mappings.length }) }}
              </span>
            </div>
            <p class="text-[11px] text-indigo-700">{{ t('products.factory_pn_desc') }}</p>
            <!-- Edit mode: mapping manager -->
            <div v-if="isEdit && initialData?.id" class="space-y-3 pt-1">
              <div v-if="isLoadingMappings" class="text-xs text-slate-500 py-1">{{ t('products.loading_mappings') }}</div>
              <div v-else-if="mappings.length > 0" class="flex flex-wrap gap-2 max-h-36 overflow-y-auto p-1 bg-white/70 rounded-xl border border-indigo-100">
                <div v-for="m in mappings" :key="m.id" class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white border border-indigo-200 text-xs font-mono font-bold text-slate-800 shadow-xs">
                  <span>{{ m.internal_factory_part_number }}</span>
                  <span class="text-[10px] px-1 py-0.2 bg-indigo-50 text-indigo-600 rounded font-sans font-normal">{{ m.source_drawing_code }}</span>
                  <button type="button" @click="deleteMapping(m.id)" class="text-slate-400 hover:text-rose-600 ml-1 transition-colors cursor-pointer" title="Delete"><i class="fas fa-times"></i></button>
                </div>
              </div>
              <div v-else class="text-xs text-slate-500 italic py-1">{{ t('products.no_mappings') }}</div>
              <div class="pt-2 border-t border-indigo-100 space-y-2">
                <div class="flex items-center gap-2">
                  <input v-model="newPartNumber" type="text" :placeholder="t('products.new_pn_placeholder')" class="flex-1 p-2 rounded-xl border border-indigo-200 bg-white font-mono text-xs font-bold uppercase outline-none focus:ring-2 focus:ring-indigo-400" @keydown.enter.prevent="addMapping" />
                  <select v-model="newDrawingCode" class="p-2 rounded-xl border border-indigo-200 bg-white text-xs font-medium outline-none">
                    <option value="PD014736">PD014736 (erro_01)</option>
                    <option value="PD027504">PD027504 (erro_02)</option>
                    <option value="PD024364">PD024364 (erro_03)</option>
                    <option value="PD027032">PD027032 (erro_04)</option>
                    <option value="PD016906">PD016906 (erro_05)</option>
                    <option value="LEGACY">LEGACY</option>
                  </select>
                  <button type="button" @click="addMapping" :disabled="!newPartNumber.trim() || isAddingMapping" class="px-3 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white text-xs font-bold rounded-xl transition-colors cursor-pointer shrink-0">
                    {{ isAddingMapping ? t('products.adding_mapping') : t('products.add_mapping_btn') }}
                  </button>
                </div>
                <div v-if="mappingError" class="text-xs font-semibold text-rose-600">{{ mappingError }}</div>
              </div>
            </div>
            <!-- Create mode: initial P/N -->
            <div v-else class="space-y-1">
              <input v-model="formData.internal_factory_part_number" type="text" :placeholder="t('products.initial_pn_placeholder')" class="w-full p-2.5 rounded-xl border border-indigo-200 bg-white font-mono text-xs font-bold uppercase" />
              <p class="text-[10px] text-indigo-600">{{ t('products.initial_pn_hint') }}</p>
            </div>
          </div>

          <!-- Template-specific fields (Erro 01-05, Standard/UI) -->
          <ProductErroFields
            :templateType="formData.template_type"
            :packingMode="formData.packing_mode"
            :formData="formData"
            @update:formData="formData = $event"
          />
        </div>

        <!-- Actions -->
        <div class="pt-4 flex gap-3 border-t border-slate-100">
          <button type="button" @click="$emit('close')" class="flex-1 px-4 py-3 rounded-xl border border-slate-200 font-bold text-slate-600 hover:bg-slate-50 transition-colors cursor-pointer text-sm">
            {{ t('products.cancel_btn') }}
          </button>
          <button type="submit" :disabled="isSubmitting" class="flex-1 px-4 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold transition-all shadow-md shadow-indigo-200 disabled:opacity-50 cursor-pointer text-sm flex items-center justify-center gap-2">
            <i v-if="isSubmitting" class="fas fa-spinner fa-spin"></i>
            <span>{{ isSubmitting ? t('products.saving') : (isEdit ? t('products.update_btn') : t('products.save_btn')) }}</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { X } from 'lucide-vue-next';
import { useI18n } from 'vue-i18n';
import { useProductForm, type ProductFormData } from '../composables/useProductForm';
import catalogApi from '../api';
import type { Customer, Product, ProductInternalFactoryPartNumber } from '../../../types/api';
import ProductErroFields from './ProductErroFields.vue';

export type { ProductFormData };

const props = defineProps<{
  show: boolean;
  isEdit: boolean;
  isSubmitting: boolean;
  customers: Customer[];
  initialData?: Product | null;
}>();

const emit = defineEmits<{
  (e: 'close'): void;
  (e: 'submit', data: ProductFormData): void;
}>();

const { t } = useI18n();

const {
  formData,
  UI_TEMPLATES,
  isErroProduct,
  setPackingMode,
  onCustomerChange,
  onTemplateTypeChange,
  handleSubmit,
} = useProductForm(props, (_event, data) => emit('submit', data));

const mappings = ref<ProductInternalFactoryPartNumber[]>([]);
const isLoadingMappings = ref(false);
const isAddingMapping = ref(false);
const mappingError = ref('');
const newPartNumber = ref('');
const newDrawingCode = ref('PD014736');

const erroTemplateName = computed(() => {
  const map: Record<string, string> = { erro_01: 'erro_01.btw', erro_02: 'erro_02.btw', erro_03: 'erro_03.btw', erro_04: 'erro_04.btw', erro_05: 'erro_05.btw' };
  return map[formData.value.template_type] || 'erro_01.btw';
});

const erroTemplateLabel = computed(() => {
  const map: Record<string, string> = {
    erro_01: 'Erro 01 Thùng Carton SN',
    erro_02: 'Erro 02 Pallet SSCC & ASIN',
    erro_03: 'Erro 03 Luxshare NME',
    erro_04: 'Erro 04 PD027032',
    erro_05: 'Erro 05 Pegatron NN9',
  };
  return map[formData.value.template_type] || 'Erro 01';
});

const defaultDrawingForTemplate = (tmpl?: string) => {
  const map: Record<string, string> = { erro_01: 'PD014736', erro_02: 'PD027504', erro_03: 'PD024364', erro_04: 'PD027032', erro_05: 'PD016906' };
  return map[tmpl || ''] || 'LEGACY';
};

const loadMappings = async () => {
  if (!props.initialData?.id || !props.isEdit) { mappings.value = []; return; }
  isLoadingMappings.value = true;
  mappingError.value = '';
  try {
    const res = await catalogApi.getInternalFactoryPartNumbers(props.initialData.id);
    mappings.value = res.data || [];
  } catch (err: any) {
    console.warn('Could not load mappings:', err);
  } finally {
    isLoadingMappings.value = false;
  }
};

const addMapping = async () => {
  const code = newPartNumber.value.trim().toUpperCase();
  if (!code || !props.initialData?.id || isAddingMapping.value) return;
  isAddingMapping.value = true;
  mappingError.value = '';
  try {
    const res = await catalogApi.addInternalFactoryPartNumber(props.initialData.id, { internal_factory_part_number: code, source_drawing_code: newDrawingCode.value });
    mappings.value.push(res.data);
    newPartNumber.value = '';
  } catch (err: any) {
    mappingError.value = err.response?.data?.error || err.response?.data?.detail || 'Cannot add Factory P/N.';
  } finally {
    isAddingMapping.value = false;
  }
};

const deleteMapping = async (mappingId: number) => {
  if (!props.initialData?.id) return;
  try {
    await catalogApi.deleteInternalFactoryPartNumber(props.initialData.id, mappingId);
    mappings.value = mappings.value.filter(m => m.id !== mappingId);
  } catch (err: any) {
    mappingError.value = err.response?.data?.error || err.response?.data?.detail || 'Cannot delete Factory P/N.';
  }
};

watch(
  () => [props.show, props.initialData?.id] as const,
  ([show, id]) => {
    if (show && id && props.isEdit) {
      newDrawingCode.value = defaultDrawingForTemplate(props.initialData?.template_type);
      loadMappings();
    } else {
      mappings.value = [];
      newPartNumber.value = '';
      mappingError.value = '';
    }
  },
  { immediate: true }
);

watch(
  () => formData.value.template_type,
  (tmpl) => { newDrawingCode.value = defaultDrawingForTemplate(tmpl); }
);
</script>
