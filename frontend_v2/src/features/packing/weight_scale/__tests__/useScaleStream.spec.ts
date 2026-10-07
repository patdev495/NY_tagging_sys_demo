import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useScaleStream } from '../composables/useScaleStream';
import scaleApi from '../../scaleApi';

vi.mock('../../scaleApi', () => ({
  default: {
    getScaleCurrent: vi.fn(),
    getScaleStatus: vi.fn(),
  },
}));

describe('useScaleStream Composable', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('initializes with default scale state', () => {
    const { isAgentOnline, scaleReading, scaleStatus } = useScaleStream(() => 'http://127.0.0.1:8080');

    expect(isAgentOnline.value).toBe(false);
    expect(scaleReading.value.weight).toBe(0.0);
    expect(scaleReading.value.unit).toBe('kg');
    expect(scaleStatus.value.connected).toBe(false);
  });

  it('updates reading and status on successful poll', async () => {
    vi.mocked(scaleApi.getScaleCurrent).mockResolvedValueOnce({
      weight: 12.503,
      unit: 'kg',
      is_stable: true,
      is_tare: false,
      is_net: false,
      connected: true,
      is_streaming: true,
    });

    const { isAgentOnline, scaleReading, scaleStatus, pollScale } = useScaleStream(() => 'http://127.0.0.1:8080');

    await pollScale(true);

    expect(isAgentOnline.value).toBe(true);
    expect(scaleReading.value.weight).toBe(12.503);
    expect(scaleReading.value.is_stable).toBe(true);
    expect(scaleStatus.value.connected).toBe(true);
  });

  it('handles polling failure and sets offline state', async () => {
    vi.mocked(scaleApi.getScaleCurrent).mockRejectedValueOnce(new Error('Network error'));

    const { isAgentOnline, scaleStatus, pollScale } = useScaleStream(() => 'http://127.0.0.1:8080');

    await pollScale(true);

    expect(isAgentOnline.value).toBe(false);
    expect(scaleStatus.value.connected).toBe(false);
  });
});
