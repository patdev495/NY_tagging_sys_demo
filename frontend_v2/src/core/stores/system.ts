import { defineStore } from 'pinia';
import { ref } from 'vue';
import printApi from '../../features/print/api';

interface Notification {
  text: string;
  type: 'info' | 'success' | 'warning' | 'error';
}

export const useSystemStore = defineStore('system', () => {
  const isOnline = ref<boolean>(false);
  const isAgentConnected = ref<boolean>(true); 
  const isSidebarCollapsed = ref<boolean>(false);
  const stationId = ref<string>('Detecting...');
  const notification = ref<Notification | null>(null);
  let notificationTimer: ReturnType<typeof setTimeout> | null = null;

  function showNotification(text: string, type: Notification['type'] = 'info', duration: number = 3000) {
    if (notificationTimer) clearTimeout(notificationTimer);
    notification.value = { text, type };
    if (duration > 0) {
      notificationTimer = setTimeout(() => {
        notification.value = null;
      }, duration);
    }
  }

  function clearNotification() {
    if (notificationTimer) clearTimeout(notificationTimer);
    notification.value = null;
  }

  async function initStationId() {
    try {
      const res = await printApi.whoami();
      if (res.data?.ip) {
        stationId.value = res.data.ip;
      }
    } catch (e) {
      console.warn('Failed to detect client IP:', e);
      stationId.value = 'Unknown IP';
    }
  }

  // Initialize on load
  initStationId();

  return {
    isOnline,
    isAgentConnected,
    isSidebarCollapsed,
    stationId,
    notification,
    showNotification,
    clearNotification,
    initStationId
  };
});
