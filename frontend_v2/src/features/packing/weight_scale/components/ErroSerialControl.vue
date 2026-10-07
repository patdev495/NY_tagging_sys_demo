<template>
  <div class="rounded-xl border-2 border-indigo-300/70 bg-gradient-to-br from-indigo-950 to-slate-900 shadow-lg shadow-indigo-950/40 flex flex-col md:flex-row md:items-center justify-between px-4 py-2.5 gap-2 relative overflow-hidden shrink-0">
    <!-- Subtle glow -->
    <div class="absolute -right-8 -top-8 w-32 h-32 rounded-full bg-indigo-500/20 blur-2xl pointer-events-none"></div>

    <!-- Label + SN Preview -->
    <div class="flex flex-col min-w-0 z-10">
      <div class="flex items-center gap-2 mb-0.5">
        <div class="w-5 h-5 rounded bg-indigo-500/30 border border-indigo-400/40 flex items-center justify-center text-indigo-300 text-[10px] font-black shrink-0">#</div>
        <span class="text-[10px] font-extrabold uppercase tracking-widest text-indigo-300">{{ t('erro.next_carton_serial') }}</span>
        <span class="px-1.5 py-px rounded text-[9px] font-black uppercase shrink-0 bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
          {{ t('erro.auto_increment') }}
        </span>
      </div>
      <!-- Big SN Text -->
      <span class="font-mono font-black text-xl md:text-2xl text-white tracking-tight leading-none select-all truncate" :title="currentSNPreview">
        {{ currentSNPreview }}
      </span>
    </div>

    <!-- SOP Damaged Label Guidance Note -->
    <div class="z-10 flex items-center gap-1.5 bg-white/5 border border-white/10 rounded-lg px-2.5 py-1.5 text-slate-300 text-[11px] font-medium shrink-0">
      <span class="text-amber-400">💡</span>
      <span><strong>{{ t('erro.note') }}</strong> {{ t('erro.damaged_label_guidance') }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

defineProps<{
  currentSNPreview: string;
}>();
</script>
