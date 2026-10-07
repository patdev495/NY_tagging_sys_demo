<template>
  <!-- Variant: Sidebar -->
  <button
    v-if="variant === 'sidebar'"
    type="button"
    @click="settings.toggleLanguage()"
    class="w-full flex items-center gap-3 p-3 rounded-lg transition-all hover:bg-white/10 group text-white text-left cursor-pointer border-none bg-transparent"
    :title="settings.language === 'vi' ? t('header.switch_to_english') : t('header.switch_to_vietnamese')"
    aria-label="Toggle language"
  >
    <div class="relative flex items-center justify-center w-6 h-6 flex-shrink-0">
      <i class="fas fa-globe text-base text-indigo-300 group-hover:text-white transition-colors"></i>
    </div>
    
    <div v-if="!isCollapsed" class="flex-1 flex items-center justify-between overflow-hidden">
      <span class="font-medium whitespace-nowrap text-sm text-slate-200 group-hover:text-white">
        {{ t('common.language') || (settings.language === 'vi' ? 'Ngôn ngữ' : 'Language') }}
      </span>
      <div class="inline-flex items-center p-0.5 rounded-md bg-black/30 border border-white/15 text-[10px] font-black">
        <span :class="['px-1.5 py-0.5 rounded transition-all', settings.language === 'vi' ? 'bg-indigo-500 text-white shadow-xs' : 'text-slate-400']">VI</span>
        <span :class="['px-1.5 py-0.5 rounded transition-all', settings.language === 'en' ? 'bg-emerald-500 text-white shadow-xs' : 'text-slate-400']">EN</span>
      </div>
    </div>
  </button>

  <!-- Variant: Dark (e.g. LoginPage) -->
  <button
    v-else-if="variant === 'dark'"
    type="button"
    @click="settings.toggleLanguage()"
    class="inline-flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/10 hover:bg-white/20 border border-white/15 text-white text-xs font-bold backdrop-blur-md transition-all duration-200 cursor-pointer shadow-lg active:scale-95"
    :title="settings.language === 'vi' ? t('header.switch_to_english') : t('header.switch_to_vietnamese')"
    aria-label="Toggle language"
  >
    <i class="fas fa-globe text-indigo-300 text-xs"></i>
    <div class="inline-flex items-center text-[10px] font-black tracking-wider">
      <span :class="['px-1 py-0.5 rounded', settings.language === 'vi' ? 'bg-indigo-500 text-white' : 'text-slate-400']">VI</span>
      <span class="text-white/40 px-0.5">/</span>
      <span :class="['px-1 py-0.5 rounded', settings.language === 'en' ? 'bg-emerald-500 text-white' : 'text-slate-400']">EN</span>
    </div>
  </button>

  <!-- Variant: Header / Standard (AppHeader, ErroHeader, CustomerSelectPage) -->
  <button
    v-else
    type="button"
    @click="settings.toggleLanguage()"
    class="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs font-bold transition-all duration-200 cursor-pointer shadow-xs select-none active:scale-95"
    :class="settings.language === 'en'
      ? 'bg-emerald-50 border-emerald-300 text-emerald-800 hover:bg-emerald-100 hover:border-emerald-400'
      : 'bg-indigo-50 border-indigo-200 text-indigo-700 hover:bg-indigo-100 hover:border-indigo-300'"
    :title="settings.language === 'vi' ? t('header.switch_to_english') : t('header.switch_to_vietnamese')"
    aria-label="Toggle language"
  >
    <i class="fas fa-globe text-xs" :class="settings.language === 'en' ? 'text-emerald-600' : 'text-indigo-600'"></i>
    <div class="inline-flex items-center font-black text-[11px] font-mono leading-none">
      <span :class="settings.language === 'vi' ? 'text-indigo-900 font-extrabold underline decoration-2 decoration-indigo-500' : 'text-slate-400'">VI</span>
      <span class="text-slate-300 mx-0.5">|</span>
      <span :class="settings.language === 'en' ? 'text-emerald-800 font-extrabold underline decoration-2 decoration-emerald-600' : 'text-slate-400'">EN</span>
    </div>
  </button>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { useSettingsStore } from '../stores/settings';

withDefaults(
  defineProps<{
    variant?: 'header' | 'sidebar' | 'dark' | 'floating';
    isCollapsed?: boolean;
  }>(),
  {
    variant: 'header',
    isCollapsed: false,
  }
);

const { t } = useI18n();
const settings = useSettingsStore();
</script>
