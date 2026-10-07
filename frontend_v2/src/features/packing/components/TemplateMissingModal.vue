<template>
  <div
    v-if="show"
    class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200"
    @click.self="$emit('close')"
  >
    <div
      class="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-md overflow-hidden flex flex-col transform transition-all animate-in zoom-in-95 duration-200"
    >
      <!-- Header with Icon -->
      <div class="px-5 pt-5 pb-4 flex items-start gap-3.5 border-b border-slate-100 bg-amber-50/70">
        <div class="w-10 h-10 rounded-xl bg-amber-500 text-white flex items-center justify-center shrink-0 shadow-xs shadow-amber-500/30">
          <i class="fas fa-file-circle-exclamation text-lg"></i>
        </div>
        <div class="flex-1 min-w-0">
          <h3 class="text-base font-black text-slate-900 tracking-tight">
            {{ t('packing.template_not_found_title') }}
          </h3>
          <p class="text-xs text-amber-800 font-medium mt-0.5">
            {{ t('packing.template_not_found_desc') }}
          </p>
        </div>
        <button
          @click="$emit('close')"
          class="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-200/50 transition-colors cursor-pointer"
        >
          <i class="fas fa-times text-sm"></i>
        </button>
      </div>

      <!-- Content -->
      <div class="p-5 flex flex-col gap-3.5 text-xs">
        <!-- Target Filename Box -->
        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl flex flex-col gap-1">
          <span class="text-[11px] uppercase tracking-wider font-bold text-slate-500">
            {{ t('packing.target_file') }}
          </span>
          <div class="flex items-center gap-2">
            <i class="fas fa-file-lines text-amber-600 text-sm"></i>
            <span class="font-mono font-black text-sm text-slate-900 select-all">
              {{ filename || 'carton_base.btw' }}
            </span>
          </div>
        </div>

        <!-- Target Directory Box -->
        <div class="p-3 bg-slate-50 border border-slate-200 rounded-xl flex flex-col gap-1">
          <span class="text-[11px] uppercase tracking-wider font-bold text-slate-500">
            {{ t('packing.target_folder') }}
          </span>
          <div class="flex items-center gap-2">
            <i class="fas fa-folder-tree text-blue-600 text-sm"></i>
            <span class="font-mono text-[11px] font-bold text-slate-800 break-all select-all">
              {{ folder || 'D:\\PAT\\Templates' }}
            </span>
          </div>
        </div>

        <!-- Instruction Note -->
        <div class="p-3 bg-blue-50 border border-blue-200 rounded-xl text-blue-900 flex items-start gap-2">
          <i class="fas fa-circle-info text-blue-600 mt-0.5 text-xs"></i>
          <span class="leading-relaxed">
            {{ t('packing.template_instruction') }}
          </span>
        </div>

        <!-- Inline Error if any -->
        <div v-if="errorMessage" class="p-2.5 bg-rose-50 border border-rose-200 rounded-lg text-rose-700 text-[11px] font-semibold flex items-center gap-2">
          <i class="fas fa-triangle-exclamation text-rose-500"></i>
          <span>{{ errorMessage }}</span>
        </div>
      </div>

      <!-- Action Footer -->
      <div class="px-5 py-3.5 bg-slate-50 border-t border-slate-200 flex items-center justify-between gap-2">
        <button
          type="button"
          @click="$emit('openFolder')"
          :disabled="isOpeningFolder"
          class="px-3 py-2 rounded-xl bg-white hover:bg-slate-100 border border-slate-300 text-slate-700 font-bold text-xs flex items-center gap-1.5 transition-all shadow-xs cursor-pointer hover:border-slate-400 disabled:opacity-50"
          :title="t('packing.open_template_folder_title')"
        >
          <i v-if="isOpeningFolder" class="fas fa-spinner fa-spin text-blue-600"></i>
          <i v-else class="fas fa-folder-open text-amber-500"></i>
          <span>{{ t('packing.open_folder_btn') }}</span>
        </button>

        <div class="flex items-center gap-2">
          <button
            type="button"
            @click="$emit('close')"
            class="px-3 py-2 rounded-xl bg-slate-200 hover:bg-slate-300 text-slate-700 font-bold text-xs transition-colors cursor-pointer"
          >
            {{ t('common.close') }}
          </button>
          <button
            type="button"
            @click="$emit('retry')"
            :disabled="isRetrying"
            class="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 active:scale-95 text-white font-bold text-xs flex items-center gap-1.5 transition-all shadow-xs shadow-indigo-600/20 cursor-pointer disabled:opacity-50"
          >
            <i v-if="isRetrying" class="fas fa-spinner fa-spin"></i>
            <i v-else class="fas fa-rotate-right"></i>
            <span>{{ t('common.retry') }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

defineProps<{
  show: boolean;
  filename: string;
  folder: string;
  errorMessage?: string;
  isOpeningFolder?: boolean;
  isRetrying?: boolean;
}>();

defineEmits<{
  (e: 'close'): void;
  (e: 'openFolder'): void;
  (e: 'retry'): void;
}>();
</script>
