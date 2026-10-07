<template>
  <!-- Fields for Erro 05 (PD016906 Pegatron NN9) -->
  <div v-if="templateType === 'erro_05'" class="p-4 bg-emerald-50/60 rounded-2xl border border-emerald-200 space-y-3">
    <div class="flex items-center justify-between">
      <span class="text-xs font-bold uppercase text-emerald-900 flex items-center gap-1.5">
        <i class="fas fa-microchip text-emerald-600"></i>
        <span>{{ t('products.erro_05_title') }}</span>
      </span>
      <span class="text-[10px] text-emerald-700 font-semibold bg-emerald-100 px-2 py-0.5 rounded">PD016906 Rev I</span>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
      <div class="space-y-1">
        <label class="text-[11px] font-bold text-slate-700 uppercase">{{ t('products.pkg_prefix_label') }} *</label>
        <input :value="formData.pkg_prefix" @input="emit('update:formData', { ...formData, pkg_prefix: ($event.target as HTMLInputElement).value })" type="text" placeholder="MC220TW1" class="w-full p-2.5 rounded-xl border border-emerald-200 bg-white font-mono text-xs font-bold uppercase" />
      </div>
    </div>
    <div class="space-y-1">
      <label class="text-[11px] font-bold text-slate-700 uppercase">{{ t('products.desc_label') }} *</label>
      <textarea :value="formData.product_desc" @input="emit('update:formData', { ...formData, product_desc: ($event.target as HTMLTextAreaElement).value })" rows="2" placeholder="X LED CABLE 30AWG 230mm" class="w-full p-2.5 rounded-xl border border-emerald-200 bg-white font-mono text-xs font-medium"></textarea>
    </div>
  </div>

  <!-- Fields for Erro 04 (PD027032) -->
  <div v-else-if="templateType === 'erro_04'" class="p-4 bg-rose-50/60 rounded-2xl border border-rose-200 space-y-3">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
      <div class="space-y-1"><label class="text-[11px] font-bold text-slate-700 uppercase">{{ t('products.erro_04_src_code') }}</label><input :value="formData.factory_item_code" @input="emit('update:formData', { ...formData, factory_item_code: ($event.target as HTMLInputElement).value })" required placeholder="115-00020" class="w-full p-2.5 rounded-xl border border-rose-200 bg-white font-mono text-xs font-bold" /></div>
      <div class="space-y-1"><label class="text-[11px] font-bold text-slate-700 uppercase">Carton ID Prefix *</label><select :value="formData.carton_id_prefix" @change="emit('update:formData', { ...formData, carton_id_prefix: ($event.target as HTMLSelectElement).value as 'H'|'K'|'' })" required class="w-full p-2.5 rounded-xl border border-rose-200 bg-white font-mono text-xs font-bold"><option disabled value="">{{ t('products.select_hk') }}</option><option value="H">H - CAT6A</option><option value="K">K - CAT5E</option></select></div>
      <div class="space-y-1"><label class="text-[11px] font-bold text-slate-700 uppercase">UPC *</label><input :value="formData.upc" @input="emit('update:formData', { ...formData, upc: ($event.target as HTMLInputElement).value })" required class="w-full p-2.5 rounded-xl border border-rose-200 bg-white font-mono text-xs font-bold" /></div>
      <div class="space-y-1"><label class="text-[11px] font-bold text-slate-700 uppercase">Supplier PN *</label><input :value="formData.mfr_pn" @input="emit('update:formData', { ...formData, mfr_pn: ($event.target as HTMLInputElement).value })" required class="w-full p-2.5 rounded-xl border border-rose-200 bg-white font-mono text-xs font-bold" /></div>
      <div class="space-y-1"><label class="text-[11px] font-bold text-slate-700 uppercase">Revision *</label><input :value="formData.revision" @input="emit('update:formData', { ...formData, revision: ($event.target as HTMLInputElement).value })" required class="w-full p-2.5 rounded-xl border border-rose-200 bg-white font-mono text-xs font-bold" /></div>
    </div>
    <div class="space-y-1"><label class="text-[11px] font-bold text-slate-700 uppercase">SKU Description *</label><textarea :value="formData.product_desc" @input="emit('update:formData', { ...formData, product_desc: ($event.target as HTMLTextAreaElement).value })" required rows="2" class="w-full p-2.5 rounded-xl border border-rose-200 bg-white font-mono text-xs"></textarea></div>
  </div>

  <!-- Fields for Erro 03 (PD024364) -->
  <div v-else-if="templateType === 'erro_03'" class="p-4 bg-amber-50/60 rounded-2xl border border-amber-200 space-y-3">
    <div class="flex items-center justify-between">
      <span class="text-xs font-bold uppercase text-amber-900 flex items-center gap-1.5"><i class="fas fa-industry text-amber-600"></i><span>{{ t('products.erro_03_title') }}</span></span>
      <span class="text-[10px] text-amber-700 font-semibold bg-amber-100 px-2 py-0.5 rounded">PD024364 REV.M</span>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
      <div class="space-y-1"><label class="text-[11px] font-bold text-slate-700 uppercase">{{ t('products.supplier_code') }} *</label><input :value="formData.pkg_prefix" @input="emit('update:formData', { ...formData, pkg_prefix: ($event.target as HTMLInputElement).value })" type="text" placeholder="1012665" class="w-full p-2.5 rounded-xl border border-amber-200 bg-white font-mono text-xs font-bold" /></div>
      <div class="space-y-1"><label class="text-[11px] font-bold text-slate-700 uppercase">APN-Rev</label><input :value="formData.revision" @input="emit('update:formData', { ...formData, revision: ($event.target as HTMLInputElement).value })" type="text" placeholder="/" class="w-full p-2.5 rounded-xl border border-amber-200 bg-white font-mono text-xs font-bold uppercase" /></div>
      <div class="space-y-1"><label class="text-[11px] font-bold text-slate-700 uppercase">{{ t('products.luxshare_pn') }} *</label><input :value="formData.luxshare_part_number" @input="emit('update:formData', { ...formData, luxshare_part_number: ($event.target as HTMLInputElement).value })" required type="text" placeholder="LLERJ014-NC-R" class="w-full p-2.5 rounded-xl border border-amber-200 bg-white font-mono text-xs font-bold" /></div>
      <div class="space-y-1"><label class="text-[11px] font-bold text-slate-700 uppercase">Customer Project *</label><input :value="formData.customer_project" @input="emit('update:formData', { ...formData, customer_project: ($event.target as HTMLInputElement).value })" required type="text" placeholder="Andy Town/ Firefly" class="w-full p-2.5 rounded-xl border border-amber-200 bg-white font-mono text-xs font-bold" /></div>
      <div class="space-y-1"><label class="text-[11px] font-bold text-slate-700 uppercase">Production Stage *</label><input :value="formData.production_stage" @input="emit('update:formData', { ...formData, production_stage: ($event.target as HTMLInputElement).value })" required type="text" placeholder="MP" class="w-full p-2.5 rounded-xl border border-amber-200 bg-white font-mono text-xs font-bold uppercase" /></div>
    </div>
    <div class="space-y-1"><label class="text-[11px] font-bold text-slate-700 uppercase">{{ t('products.desc_label') }} *</label><textarea :value="formData.product_desc" @input="emit('update:formData', { ...formData, product_desc: ($event.target as HTMLTextAreaElement).value })" rows="2" placeholder="CAT5E ETHERNET CABLE" class="w-full p-2.5 rounded-xl border border-amber-200 bg-white font-mono text-xs font-medium"></textarea></div>
  </div>

  <!-- Fields for Erro 02 (PD027504) -->
  <div v-else-if="templateType === 'erro_02'" class="p-4 bg-sky-50/60 rounded-2xl border border-sky-200 space-y-3">
    <div class="flex items-center justify-between">
      <span class="text-xs font-bold uppercase text-sky-900 flex items-center gap-1.5"><i class="fas fa-barcode text-sky-600"></i><span>{{ t('products.erro_02_title') }}</span></span>
      <span class="text-[10px] text-sky-700 font-semibold bg-sky-100 px-2 py-0.5 rounded">PD027504</span>
    </div>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
      <div class="space-y-1"><label class="text-[11px] font-bold text-slate-700 uppercase">Amazon ASIN *</label><input :value="formData.asin" @input="emit('update:formData', { ...formData, asin: ($event.target as HTMLInputElement).value })" type="text" placeholder="B08G9M4HXS" class="w-full p-2.5 rounded-xl border border-sky-200 bg-white font-mono text-xs font-bold uppercase" /></div>
      <div class="space-y-1"><label class="text-[11px] font-bold text-slate-700 uppercase">Unit UPC Barcode *</label><input :value="formData.upc" @input="emit('update:formData', { ...formData, upc: ($event.target as HTMLInputElement).value })" type="text" placeholder="852582006785" class="w-full p-2.5 rounded-xl border border-sky-200 bg-white font-mono text-xs font-bold" /></div>
      <div class="space-y-1"><label class="text-[11px] font-bold text-slate-700 uppercase">P/N (Spec No) *</label><input :value="formData.mfr_pn" @input="emit('update:formData', { ...formData, mfr_pn: ($event.target as HTMLInputElement).value })" type="text" placeholder="NYS5998" class="w-full p-2.5 rounded-xl border border-sky-200 bg-white font-mono text-xs font-bold" /></div>
      <div class="space-y-1"><label class="text-[11px] font-bold text-slate-700 uppercase">SSCC Company Prefix *</label><input :value="formData.pkg_prefix" @input="emit('update:formData', { ...formData, pkg_prefix: ($event.target as HTMLInputElement).value })" type="text" placeholder="37033907" class="w-full p-2.5 rounded-xl border border-sky-200 bg-white font-mono text-xs font-bold" /></div>
    </div>
    <div class="space-y-1"><label class="text-[11px] font-bold text-slate-700 uppercase">{{ t('products.desc_label') }} *</label><textarea :value="formData.product_desc" @input="emit('update:formData', { ...formData, product_desc: ($event.target as HTMLTextAreaElement).value })" rows="2" placeholder="ASSY,BAND WRAPPED..." class="w-full p-2.5 rounded-xl border border-sky-200 bg-white font-mono text-xs font-medium"></textarea></div>
  </div>

  <!-- Fields for Erro 01 / yearly prefix -->
  <div v-else-if="templateType === 'erro_01' || packingMode === 'weight_scale'" class="grid grid-cols-1 md:grid-cols-3 gap-3 p-4 bg-purple-50/50 rounded-2xl border border-purple-100">
    <div class="space-y-1">
      <label class="text-[11px] font-bold text-slate-700 uppercase">PKG Prefix (Carton SN) *</label>
      <input :value="formData.pkg_prefix" @input="emit('update:formData', { ...formData, pkg_prefix: ($event.target as HTMLInputElement).value })" type="text" placeholder="VHK0010237" class="w-full p-2.5 rounded-xl border border-purple-200 bg-white font-mono text-xs font-bold" />
      <p class="text-[10px] text-slate-400">{{ t('products.pkg_prefix_hint') }}</p>
    </div>
    <div class="space-y-1">
      <label class="text-[11px] font-bold text-slate-700 uppercase">MFR P/N (Spec No) *</label>
      <input :value="formData.mfr_pn" @input="emit('update:formData', { ...formData, mfr_pn: ($event.target as HTMLInputElement).value })" type="text" placeholder="NYS5998" class="w-full p-2.5 rounded-xl border border-purple-200 bg-white font-mono text-xs font-bold" />
      <p class="text-[10px] text-slate-400">{{ t('products.mfr_pn_hint') }}</p>
    </div>
    <div class="space-y-1">
      <label class="text-[11px] font-bold text-slate-700 uppercase">Revision</label>
      <input :value="formData.revision" @input="emit('update:formData', { ...formData, revision: ($event.target as HTMLInputElement).value })" type="text" placeholder="B" class="w-full p-2.5 rounded-xl border border-purple-200 bg-white font-mono text-xs font-bold uppercase" />
      <p class="text-[10px] text-slate-400">{{ t('products.revision_hint') }}</p>
    </div>
  </div>

  <!-- Fields for Standard / UI monthly prefix -->
  <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-3 p-4 bg-slate-50 rounded-2xl border border-slate-200">
    <div class="space-y-1">
      <label class="text-[11px] font-bold text-slate-700 uppercase">S/N Start Part</label>
      <input :value="formData.start_part" @input="emit('update:formData', { ...formData, start_part: ($event.target as HTMLInputElement).value })" type="text" placeholder="VN or CN" class="w-full p-2.5 rounded-xl border border-slate-200 bg-white font-mono text-xs font-bold" />
      <p class="text-[10px] text-slate-400">{{ t('products.start_part_hint') }}</p>
    </div>
    <div class="space-y-1">
      <label class="text-[11px] font-bold text-slate-700 uppercase">S/N Middle Part</label>
      <input :value="formData.middle_part" @input="emit('update:formData', { ...formData, middle_part: ($event.target as HTMLInputElement).value })" type="text" placeholder="11, 16, A, B..." class="w-full p-2.5 rounded-xl border border-slate-200 bg-white font-mono text-xs font-bold" />
      <p class="text-[10px] text-slate-400">{{ t('products.middle_part_hint') }}</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import type { ProductFormData } from '../composables/useProductForm';

defineProps<{
  templateType: string;
  packingMode: string;
  formData: ProductFormData;
}>();

const emit = defineEmits<{
  (e: 'update:formData', data: ProductFormData): void;
}>();

const { t } = useI18n();
</script>
