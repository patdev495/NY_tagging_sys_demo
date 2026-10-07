import { ref, onMounted, onUnmounted } from 'vue';
import scaleApi from '../../scaleApi';
import type { ScaleReading, ScaleStatus } from '../../../../types/api';

export interface UseScaleStreamOptions {
  getAgentUrl?: () => string;
  autoStart?: boolean;
  onNotification?: (message: string, type: 'info' | 'success' | 'warning' | 'error') => void;
}

export function useScaleStream(
  agentUrlSource?: string | (() => string) | UseScaleStreamOptions,
  options?: UseScaleStreamOptions
) {
  let getAgentUrl: () => string;
  let autoStart = false;

  if (typeof agentUrlSource === 'function') {
    getAgentUrl = agentUrlSource;
    if (options?.autoStart !== undefined) autoStart = options.autoStart;
  } else if (typeof agentUrlSource === 'string') {
    getAgentUrl = () => agentUrlSource;
    if (options?.autoStart !== undefined) autoStart = options.autoStart;
  } else if (typeof agentUrlSource === 'object' && agentUrlSource !== null) {
    getAgentUrl = agentUrlSource.getAgentUrl || (() => 'http://127.0.0.1:8080');
    autoStart = !!agentUrlSource.autoStart;
  } else {
    getAgentUrl = () => 'http://127.0.0.1:8080';
  }

  const isAgentOnline = ref<boolean>(false);
  const scaleReading = ref<ScaleReading>({
    weight: 0.0,
    unit: 'kg',
    is_stable: false,
    is_tare: false,
    is_net: false,
  });

  const scaleStatus = ref<ScaleStatus>({
    connected: false,
    port: '',
    baudrate: 9600,
    is_streaming: false,
  });

  let scalePollInterval: any = null;
  let statusPollInterval: any = null;

  const pollScale = async (force: boolean = false) => {
    if (!isAgentOnline.value && !force) {
      return;
    }
    const agentUrl = getAgentUrl();
    try {
      const reading = await scaleApi.getScaleCurrent(agentUrl);
      if (reading) {
        isAgentOnline.value = true;
        scaleReading.value = reading;
        if (reading.connected !== undefined) {
          scaleStatus.value.connected = reading.connected;
        }
        if (reading.is_streaming !== undefined) {
          scaleStatus.value.is_streaming = reading.is_streaming;
        }
      }
    } catch {
      isAgentOnline.value = false;
      scaleStatus.value.connected = false;
      scaleStatus.value.is_streaming = false;
    }
  };

  const pollScaleStatus = async () => {
    const agentUrl = getAgentUrl();
    try {
      const status = await scaleApi.getScaleStatus(agentUrl);
      if (status) {
        isAgentOnline.value = true;
        scaleStatus.value = status;
      }
    } catch {
      isAgentOnline.value = false;
      scaleStatus.value.connected = false;
      scaleStatus.value.is_streaming = false;
    }
  };

  const startPolling = () => {
    stopPolling();
    pollScale();
    pollScaleStatus();
    scalePollInterval = setInterval(pollScale, 100);
    statusPollInterval = setInterval(pollScaleStatus, 2000);
  };

  const stopPolling = () => {
    if (scalePollInterval) {
      clearInterval(scalePollInterval);
      scalePollInterval = null;
    }
    if (statusPollInterval) {
      clearInterval(statusPollInterval);
      statusPollInterval = null;
    }
  };

  if (autoStart) {
    onMounted(() => {
      startPolling();
    });
    onUnmounted(() => {
      stopPolling();
    });
  }

  return {
    isAgentOnline,
    scaleReading,
    scaleStatus,
    pollScale,
    pollScaleStatus,
    startPolling,
    stopPolling,
  };
}
