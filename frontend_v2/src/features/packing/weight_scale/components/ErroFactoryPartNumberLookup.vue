<template>
  <form class="flex items-end gap-2" @submit.prevent="resolve">
    <label class="block">
      <span class="block text-[10px] uppercase tracking-wider font-bold text-slate-400 mb-1">Factory P/N</span>
      <input
        v-model="value"
        type="text"
        autocomplete="off"
        :placeholder="t('erro.factory_part_number_lookup_placeholder')"
        class="w-56 px-3 py-2 rounded-lg border border-slate-300 bg-white font-mono text-sm font-bold uppercase outline-none focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
        :disabled="isResolving"
      />
    </label>
    <button
      type="submit"
      class="h-9 px-3 rounded-lg bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 text-white text-xs font-bold transition-colors"
      :disabled="isResolving || !value.trim()"
    >
      {{ isResolving ? t('common.loading') : t('erro.choose_product_action') }}
    </button>
    <p v-if="error" class="max-w-60 text-xs font-semibold text-rose-700">{{ error }}</p>
    <p v-else-if="resolvedProduct" class="text-xs font-semibold text-emerald-700">
      {{ resolvedProduct.item_name }} · {{ resolvedProduct.template_type }}
    </p>
  </form>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';
import catalogApi from '../../../catalog/api';
import type { Product } from '../../../../types/api';
import { userErrorMessage } from '../../../../i18n/errorMessage';

const { t } = useI18n();

const emit = defineEmits<{
  (e: 'resolved', product: Product): void;
}>();

const value = ref('');
const error = ref('');
const isResolving = ref(false);
const resolvedProduct = ref<Product | null>(null);

const resolve = async () => {
  const factoryPartNumber = value.value.trim();
  if (!factoryPartNumber || isResolving.value) return;

  error.value = '';
  isResolving.value = true;
  try {
    const response = await catalogApi.resolveErroProductByInternalFactoryPartNumber(factoryPartNumber);
    resolvedProduct.value = response.data;
    value.value = response.data.internal_factory_part_number || factoryPartNumber.toUpperCase();
    emit('resolved', response.data);
  } catch (err: unknown) {
    resolvedProduct.value = null;
    error.value = userErrorMessage(err, t);
  } finally {
    isResolving.value = false;
  }
};
</script>
