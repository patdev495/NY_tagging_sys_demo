import { ref, type Ref, unref } from 'vue';
import type { Product } from '../../../types/api';

export interface AgentHealthSettings {
  printMode?: string;
  agentUrl?: string;
  localTemplateDir?: string;
}

export interface UseAgentHealthOptions {
  settings: AgentHealthSettings | Ref<AgentHealthSettings>;
  currentProduct: Ref<Product | null>;
}

export function useAgentHealth(options: UseAgentHealthOptions) {
  const agentConnected = ref<boolean>(true);
  const templateMissing = ref<boolean>(false);
  const templateFilename = ref<string>('');
  let agentCheckInterval: ReturnType<typeof setInterval> | null = null;

  const getSettings = (): AgentHealthSettings => {
    return unref(options.settings) || {};
  };

  const checkTemplateExists = async () => {
    const s = getSettings();
    const product = options.currentProduct.value;

    if (s.printMode !== 'local' || !agentConnected.value || !product) {
      templateMissing.value = false;
      return;
    }

    const canonicalFallback = product.template_type === 'erro_05'
      ? 'erro_05.btw'
      : (product.template_type === 'erro_04'
        ? 'erro_04.btw'
        : (product.template_type === 'erro_03'
          ? 'erro_03.btw'
          : (product.template_type === 'erro_02'
            ? 'erro_02.btw'
            : (product.template_type === 'erro_01' ? 'erro_01.btw' : 'carton_base.btw'))));
    const fullPath = product.template_path || canonicalFallback;
    const filename = fullPath.split(/[\\/]/).pop() || canonicalFallback;
    templateFilename.value = filename;

    try {
      const agentUrl = s.agentUrl || 'http://127.0.0.1:8080';
      const localDir = s.localTemplateDir || '';
      const url = `${agentUrl}/check-file?folder=${encodeURIComponent(localDir)}&filename=${encodeURIComponent(filename)}`;
      const resp = await fetch(url);
      if (resp.ok) {
        const data = await resp.json();
        templateMissing.value = !data.exists;
      }
    } catch {
      templateMissing.value = false;
    }
  };

  const checkAgentHealth = async () => {
    const s = getSettings();
    if (s.printMode !== 'local') {
      agentConnected.value = true;
      templateMissing.value = false;
      return;
    }

    try {
      const agentUrl = s.agentUrl || 'http://127.0.0.1:8080';
      // @ts-ignore
      const timeoutSignal = typeof AbortSignal !== 'undefined' && AbortSignal.timeout ? AbortSignal.timeout(6000) : undefined;
      const resp = await fetch(`${agentUrl}/status`, { signal: timeoutSignal });
      agentConnected.value = resp.ok;
      if (agentConnected.value) {
        await checkTemplateExists();
      }
    } catch {
      agentConnected.value = false;
    }
  };

  const startPolling = (intervalMs = 5000) => {
    stopPolling();
    checkAgentHealth();
    agentCheckInterval = setInterval(checkAgentHealth, intervalMs);
  };

  const stopPolling = () => {
    if (agentCheckInterval) {
      clearInterval(agentCheckInterval);
      agentCheckInterval = null;
    }
  };

  return {
    agentConnected,
    templateMissing,
    templateFilename,
    checkAgentHealth,
    checkTemplateExists,
    startPolling,
    stopPolling,
  };
}
