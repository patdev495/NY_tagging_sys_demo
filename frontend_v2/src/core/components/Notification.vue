<template>
  <Transition 
    enter-active-class="transition duration-300 ease-out"
    enter-from-class="translate-y-5 opacity-0"
    enter-to-class="translate-y-0 opacity-100"
    leave-active-class="transition duration-300 ease-in"
    leave-from-class="translate-y-0 opacity-100"
    leave-to-class="translate-y-5 opacity-0"
  >
    <div 
      v-if="system.notification" 
      class="fixed bottom-[30px] right-[30px] px-6 py-4 rounded-xl z-[3000] shadow-2xl font-medium text-white flex items-center gap-3"
      :class="{
        'bg-emerald-500': system.notification.type === 'success',
        'bg-rose-500': system.notification.type === 'error',
        'bg-amber-500': system.notification.type === 'warning',
        'bg-slate-800': !['success', 'error', 'warning'].includes(system.notification.type)
      }"
    >
      <i class="fas" :class="system.notification.type === 'success' ? 'fa-check-circle' : 'fa-exclamation-circle'"></i>
      {{ system.notification.text }}
    </div>
  </Transition>
</template>

<script setup lang="ts">
import { useSystemStore } from '../stores/system';
const system = useSystemStore();
</script>
