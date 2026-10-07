<template>
  <header class="bg-white px-3 md:px-5 py-1.5 md:py-2 flex justify-between items-center border-b border-slate-200 shadow-sm">
    <div @click="$emit('home')" class="no-underline text-inherit transition-opacity duration-200 cursor-pointer hover:opacity-80">
      <h1 class="m-0 text-[1rem] md:text-[1.1rem] font-extrabold text-slate-900 flex items-center gap-2">
        <i class="fas fa-box-open text-blue-600"></i> {{ t('header.title') }}
      </h1>
    </div>
    <div class="flex items-center gap-[10px]">
      <div 
        class="px-[10px] py-1 rounded-full text-[0.7rem] font-bold flex items-center gap-[6px] transition-colors"
        :class="system.isOnline ? 'bg-green-100 text-green-800' : 'bg-slate-100 text-slate-500'"
      >
        <span 
          class="w-1.5 h-1.5 rounded-full" 
          :class="system.isOnline ? 'bg-green-500 shadow-[0_0_8px_#22c55e]' : 'bg-slate-300'"
        ></span>
        {{ system.isOnline ? t('header.status_online') : t('header.connecting') }}
      </div>
      
      <button 
        @click="$emit('toggle-audio')" 
        class="w-9 h-9 rounded-[10px] cursor-pointer flex items-center justify-center transition-all duration-200 text-[0.9rem] border hover:bg-slate-50 hover:border-slate-300 hover:text-slate-900 hover:-translate-y-[2px]"
        :class="isAudioActive ? 'bg-blue-50 border-blue-200 text-blue-600' : 'bg-white border-slate-200 text-slate-500'" 
        :title="isAudioActive ? t('header.audio_active') : t('header.audio_inactive')"
      >
        <i class="fas" :class="isAudioActive ? 'fa-volume-up' : 'fa-volume-mute'"></i>
      </button>

      <button 
        @click="$emit('show-emergency')" 
        class="w-9 h-9 rounded-[10px] cursor-pointer flex items-center justify-center transition-all duration-200 text-[0.9rem] bg-white border border-slate-200 text-slate-500 hover:bg-rose-50 hover:border-rose-200 hover:text-rose-600 hover:-translate-y-[2px]" 
        :title="t('header.emergency_reprint')"
      >
        <i class="fas fa-exclamation-triangle"></i>
      </button>

      <div class="border-l border-slate-200 pl-3 ml-1">
        <LanguageSwitch variant="header" />
      </div>

      <button 
        @click="$emit('show-settings')" 
        class="w-9 h-9 rounded-[10px] cursor-pointer flex items-center justify-center transition-all duration-200 text-[0.9rem] bg-white border border-slate-200 text-slate-500 hover:bg-slate-50 hover:border-slate-300 hover:text-slate-900 hover:-translate-y-[2px]" 
        :title="t('header.settings')"
      >
        <i class="fas fa-cog"></i>
      </button>

      <button
        @click="switchCustomer"
        class="px-2.5 py-1.5 rounded-[10px] cursor-pointer flex items-center gap-1.5 text-[0.75rem] font-bold border bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100 hover:text-slate-900 transition-all"
        :title="t('header.switch_customer')"
      >
        <i class="fas fa-exchange-alt text-xs text-blue-600"></i>
        <span class="hidden sm:inline">{{ t('header.switch_customer') }}</span>
      </button>

      <router-link 
        to="/admin" 
        class="w-9 h-9 rounded-[10px] cursor-pointer flex items-center justify-center transition-all duration-200 text-[0.9rem] border bg-slate-50 text-indigo-600 border-indigo-200 hover:bg-indigo-50 hover:text-indigo-800 hover:-translate-y-[2px]" 
        :title="t('header.admin_dashboard')"
      >
        <i class="fas fa-user-shield"></i>
      </router-link>
    </div>
  </header>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { useSystemStore } from '../stores/system';
import { useSettingsStore } from '../stores/settings';
import LanguageSwitch from './LanguageSwitch.vue';

const router = useRouter();

defineProps<{
  isAudioActive?: boolean
}>();

const emit = defineEmits<{
  (e: 'toggle-audio'): void
  (e: 'show-emergency'): void
  (e: 'show-settings'): void
  (e: 'home'): void
}>();

const { t } = useI18n();
const system = useSystemStore();
const settings = useSettingsStore();

const toggleLanguage = () => {
  settings.language = settings.language === 'vi' ? 'en' : 'vi';
  settings.saveSettings();
};

const switchCustomer = () => {
  localStorage.removeItem('selected_customer');
  router.push('/');
};
</script>
