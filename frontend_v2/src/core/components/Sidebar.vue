<template>
  <aside 
    :class="[
      'fixed left-0 top-0 h-screen transition-all duration-300 z-50 flex flex-col shadow-[4px_0_20px_rgba(0,0,0,0.1)] bg-linear-to-b from-[#1e1b4b] to-[#0f172a] text-white',
      isCollapsed ? 'w-20' : 'w-64'
    ]"
  >
    <!-- Header/Logo -->
    <router-link to="/" class="p-6 flex items-center gap-3 border-b border-indigo-800 hover:bg-white/5 transition-colors cursor-pointer no-underline text-white">
      <div class="bg-white p-2 rounded-lg flex-shrink-0 shadow-sm">
        <Package class="text-indigo-900 w-6 h-6" />
      </div>
      <div v-if="!isCollapsed" class="overflow-hidden whitespace-nowrap">
        <h1 class="font-black tracking-tight text-xl">NY TAGGING</h1>
      </div>
    </router-link>

    <!-- Navigation -->
    <nav class="flex-1 py-6 px-3 space-y-2 overflow-y-auto">
      <router-link 
        v-for="item in menuItems" 
        :key="item.path" 
        :to="item.path"
        class="flex items-center gap-3 p-3 rounded-lg transition-all hover:bg-white/10 group text-white"
        active-class="bg-indigo-600 shadow-[0_4px_12px_rgba(79,70,229,0.3)]"
        exact-active-class="bg-indigo-600 shadow-[0_4px_12px_rgba(79,70,229,0.3)]"
        :title="isCollapsed ? item.label : ''"
      >
        <component :is="item.icon" class="w-6 h-6 flex-shrink-0" />
        <span v-if="!isCollapsed" class="font-medium whitespace-nowrap">{{ item.label }}</span>
      </router-link>

      <button
        @click="showSettings = true"
        class="w-full flex items-center gap-3 p-3 rounded-lg transition-all hover:bg-white/10 group text-white text-left cursor-pointer border-none bg-transparent"
        :title="isCollapsed ? t('nav.settings') : ''"
      >
        <Settings class="w-6 h-6 flex-shrink-0" />
        <span v-if="!isCollapsed" class="font-medium whitespace-nowrap">{{ t('nav.settings') }}</span>
      </button>

      <LanguageSwitch variant="sidebar" :is-collapsed="isCollapsed" />
    </nav>

    <!-- User Profile & Logout -->
    <div class="p-3 border-t border-indigo-800/60 flex items-center justify-between gap-2 bg-black/20">
      <div v-if="!isCollapsed" class="flex items-center gap-2.5 overflow-hidden">
        <div class="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center font-bold text-xs flex-shrink-0">
          {{ authStore.user?.username?.charAt(0).toUpperCase() || 'U' }}
        </div>
        <div class="overflow-hidden">
          <p class="m-0 text-xs font-bold truncate leading-tight">{{ authStore.user?.username || 'User' }}</p>
          <span :class="['text-[9px] font-black uppercase px-1.5 py-0.5 rounded inline-block', authStore.isAdmin ? 'bg-indigo-500 text-white' : 'bg-emerald-500 text-white']">
            {{ authStore.roleName || 'GUEST' }}
          </span>
        </div>
      </div>
      <button 
        @click="handleLogout"
        class="p-2 rounded-lg hover:bg-rose-500/20 hover:text-rose-400 text-slate-400 transition-colors cursor-pointer border-none bg-transparent flex-shrink-0"
        :title="t('nav.logout')"
      >
        <LogOut class="w-5 h-5" />
      </button>
    </div>

    <!-- Footer / Toggle -->
    <div class="p-3 border-t border-indigo-800/40">
      <button 
        @click="isCollapsed = !isCollapsed"
        class="w-full flex items-center justify-center p-2 rounded-lg hover:bg-indigo-800 transition-colors cursor-pointer border-none bg-transparent text-white"
      >
        <ChevronLeft v-if="!isCollapsed" class="w-5 h-5" />
        <ChevronRight v-else class="w-5 h-5" />
      </button>
    </div>

    <!-- Settings Modal -->
    <SettingsModal :show="showSettings" @close="showSettings = false" />
  </aside>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { 
  Package, 
  LayoutDashboard, 
  Users, 
  Box, 
  Settings, 
  BarChart3,
  ChevronLeft,
  ChevronRight,
  ClipboardList,
  LogOut,
  Layers
} from 'lucide-vue-next';
import { useSystemStore } from '../stores/system';
import { useAuthStore } from '../stores/auth';
import { useRouter } from 'vue-router';
import { storeToRefs } from 'pinia';
import type { Component } from 'vue';
import { useI18n } from 'vue-i18n';
import SettingsModal from '../../features/settings/components/SettingsModal.vue';
import LanguageSwitch from './LanguageSwitch.vue';

const systemStore = useSystemStore();
const authStore = useAuthStore();
const router = useRouter();

const { isSidebarCollapsed: isCollapsed } = storeToRefs(systemStore);
const showSettings = ref(false);

const { t } = useI18n();

const handleLogout = () => {
  authStore.logout();
  router.push('/admin/login');
};

interface MenuItem {
  label: string;
  path: string;
  icon: Component;
}

const menuItems = computed<MenuItem[]>(() => [
  { label: t('nav.packingStation'), path: '/', icon: Box },
  { label: t('nav.dashboard'), path: '/admin', icon: LayoutDashboard },
  { label: t('nav.productionRuns'), path: '/admin/production-runs', icon: Layers },
  { label: t('nav.customers'), path: '/admin/customers', icon: Users },
  { label: t('nav.products'), path: '/admin/products', icon: Package },
  { label: t('nav.cartonHistory'), path: '/admin/history', icon: ClipboardList },
  { label: t('nav.snLookup'), path: '/admin/stats', icon: BarChart3 },
]);
</script>

