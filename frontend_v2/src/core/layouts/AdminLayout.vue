<template>
  <div class="layout-wrapper flex min-h-screen bg-slate-50">
    <Sidebar />
    
    <main 
      :class="[
        'main-content flex-1 transition-all duration-300 min-w-0',
        isSidebarCollapsed ? 'ml-20' : 'ml-64'
      ]"
    >
      <!-- Page Content with Transition -->
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
import Sidebar from '../components/Sidebar.vue';
import { useSystemStore } from '../stores/system';
import { storeToRefs } from 'pinia';

const systemStore = useSystemStore();
const { isSidebarCollapsed } = storeToRefs(systemStore);
</script>

<style scoped>
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
