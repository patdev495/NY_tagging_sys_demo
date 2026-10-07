<template>
  <div class="w-full bg-white rounded-xl border border-slate-200 flex flex-col shadow-xs lg:w-[320px] xl:w-[360px] h-[380px] lg:h-[calc(100vh-140px)] lg:sticky lg:top-3 shrink-0 overflow-hidden">
    <!-- Header -->
    <div class="px-4 py-3 border-b border-slate-200 flex justify-between items-center bg-slate-50 shrink-0">
      <div class="flex items-center gap-2">
        <div class="w-2 h-2 rounded-full" :class="items.length > 0 ? 'bg-emerald-500' : 'bg-slate-300'"></div>
        <h3 class="m-0 text-sm font-bold text-slate-800 uppercase tracking-wide">
          {{ t('packing.scanned') }} ({{ items.length }})
        </h3>
      </div>
      <button 
        v-if="items.length > 0"
        @click="confirmClear" 
        class="px-2.5 py-1 text-xs font-bold text-rose-600 bg-rose-50 border border-rose-200 rounded-lg cursor-pointer transition-all hover:bg-rose-100 hover:border-rose-300 active:scale-95"
        :title="t('packing.clear_scanned_title')"
      >
        {{ t('packing.clear') }}
      </button>
    </div>

    <!-- Scanned Items List Container -->
    <div class="overflow-y-auto p-2.5 flex-1 divide-y divide-slate-100" ref="listContainer">
      <div v-if="items.length === 0" class="flex flex-col justify-center items-center h-full text-slate-400 text-xs text-center p-4">
        <div class="w-12 h-12 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-400 mb-2">
          <i class="fas fa-barcode text-xl"></i>
        </div>
        <p class="font-semibold text-slate-600 m-0 mb-1">{{ t('packing.no_scans') }}</p>
        <p class="text-[11px] text-slate-400 m-0">{{ t('packing.scan_item_hint') }}</p>
      </div>

      <div v-else class="space-y-1.5">
        <div 
          v-for="(item, idx) in displayedItems" 
          :key="idx" 
          class="flex items-center justify-between px-3 py-2 bg-slate-50/80 hover:bg-slate-100/90 rounded-lg border border-slate-200/80 transition-colors group"
        >
          <div class="flex items-center gap-2.5 min-w-0 flex-1">
            <span class="text-[11px] font-bold text-slate-500 bg-white border border-slate-200 px-1.5 py-0.5 rounded font-mono shrink-0">
              #{{ item.actualIndex + 1 }}
            </span>
            <span class="font-barcode-mono font-bold text-slate-900 text-sm truncate select-all" :title="item.sn">
              {{ item.sn }}
            </span>
          </div>

          <div class="flex items-center gap-1.5 shrink-0 ml-2">
            <!-- Latest item badge -->
            <span v-if="item.actualIndex === items.length - 1" class="text-[9px] font-black uppercase px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-300">
              {{ t('packing.latest') }}
            </span>

            <!-- Remove single item button -->
            <button 
              @click="$emit('remove-item', item.actualIndex)"
              class="w-6 h-6 rounded flex items-center justify-center text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors border border-transparent hover:border-rose-200 cursor-pointer"
              :title="t('packing.remove_scanned_title')"
            >
              <i class="fas fa-times text-xs"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer Summary -->
    <div v-if="items.length > 0" class="px-4 py-2 border-t border-slate-200 bg-slate-50/60 text-[11px] text-slate-500 flex justify-between items-center shrink-0">
      <span>{{ t('packing.last_scanned', { sn: items[items.length - 1] }) }}</span>
      <span class="font-bold text-emerald-700">{{ items.length }} pcs</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

const props = defineProps<{
  items: string[];
}>();

const emit = defineEmits<{
  (e: 'clear'): void;
  (e: 'remove-item', index: number): void;
}>();


// Display in reverse chronological order (newest on top) for fast worker verification
const displayedItems = computed(() => {
  return props.items.map((sn, idx) => ({ sn, actualIndex: idx })).reverse();
});

const confirmClear = () => {
  if (window.confirm(t('packing.clear_scanned_confirm'))) {
    emit('clear');
  }
};
</script>
