import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { ref } from 'vue';
import { useAgentHealth } from '../composables/useAgentHealth';
import type { Product } from '../../../types/api';

describe('useAgentHealth Composable', () => {
  const mockProduct: Product = {
    id: 1,
    customer_id: 1,
    item_name: 'U-Test-Product',
    packed_qty: 10,
    start_part: 'CN',
    middle_part: '11',
    template_type: 'standard',
    template_path: 'D:\\PAT\\Templates\\carton.ui.btw',
    allow_partial: 0,
  };

  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('detects agent offline when fetch fails in local mode', async () => {
    const currentProduct = ref<Product | null>(mockProduct);
    const settings = {
      printMode: 'local',
      agentUrl: 'http://127.0.0.1:8080',
      localTemplateDir: 'D:\\PAT\\Templates',
    };

    // Mock fetch to reject
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Connection refused')));

    const { agentConnected, checkAgentHealth } = useAgentHealth({
      settings,
      currentProduct,
    });

    await checkAgentHealth();

    expect(agentConnected.value).toBe(false);
  });

  it('detects agent online and checks template existence when agent responds ok', async () => {
    const currentProduct = ref<Product | null>(mockProduct);
    const settings = {
      printMode: 'local',
      agentUrl: 'http://127.0.0.1:8080',
      localTemplateDir: 'D:\\PAT\\Templates',
    };

    vi.stubGlobal('fetch', vi.fn().mockImplementation((url: string) => {
      if (url.includes('/status')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ status: 'ok' }) });
      }
      if (url.includes('/check-file')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ exists: true }) });
      }
      return Promise.reject(new Error('Unknown url'));
    }));

    const { agentConnected, templateMissing, templateFilename, checkAgentHealth } = useAgentHealth({
      settings,
      currentProduct,
    });

    await checkAgentHealth();

    expect(agentConnected.value).toBe(true);
    expect(templateMissing.value).toBe(false);
    expect(templateFilename.value).toBe('carton.ui.btw');
  });

  it('flags templateMissing when check-file reports file not existing', async () => {
    const currentProduct = ref<Product | null>(mockProduct);
    const settings = {
      printMode: 'local',
      agentUrl: 'http://127.0.0.1:8080',
      localTemplateDir: 'D:\\PAT\\Templates',
    };

    vi.stubGlobal('fetch', vi.fn().mockImplementation((url: string) => {
      if (url.includes('/status')) {
        return Promise.resolve({ ok: true });
      }
      if (url.includes('/check-file')) {
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ exists: false }) });
      }
      return Promise.reject(new Error('Unknown url'));
    }));

    const { agentConnected, templateMissing, checkAgentHealth } = useAgentHealth({
      settings,
      currentProduct,
    });

    await checkAgentHealth();

    expect(agentConnected.value).toBe(true);
    expect(templateMissing.value).toBe(true);
  });

  it('checks the canonical Erro 04 template when the Product has no explicit path', async () => {
    const currentProduct = ref<Product | null>({
      id: 4,
      customer_id: 1,
      item_name: 'G111A1A',
      packed_qty: 120,
      template_type: 'erro_04',
      allow_partial: 0,
    });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({ exists: true }) }));

    const { templateFilename, checkTemplateExists } = useAgentHealth({
      settings: { printMode: 'local', localTemplateDir: 'D:\\PAT\\Templates' },
      currentProduct,
    });
    await checkTemplateExists();

    expect(templateFilename.value).toBe('erro_04.btw');
  });

  it('bypasses check when printMode is server', async () => {
    const currentProduct = ref<Product | null>(mockProduct);
    const settings = {
      printMode: 'server',
      agentUrl: 'http://127.0.0.1:8080',
      localTemplateDir: 'D:\\PAT\\Templates',
    };

    const fetchSpy = vi.fn();
    vi.stubGlobal('fetch', fetchSpy);

    const { agentConnected, templateMissing, checkAgentHealth } = useAgentHealth({
      settings,
      currentProduct,
    });

    await checkAgentHealth();

    expect(agentConnected.value).toBe(true);
    expect(templateMissing.value).toBe(false);
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
