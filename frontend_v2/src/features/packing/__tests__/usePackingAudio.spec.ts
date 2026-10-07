import { describe, it, expect, vi, beforeEach } from 'vitest';
import { usePackingAudio } from '../composables/usePackingAudio';

describe('usePackingAudio Composable', () => {
  let mockOscillator: any;
  let mockGain: any;
  let mockAudioContextInstance: any;

  beforeEach(() => {
    mockOscillator = {
      connect: vi.fn(),
      type: 'sine',
      frequency: { setValueAtTime: vi.fn() },
      start: vi.fn(),
      stop: vi.fn(),
    };

    mockGain = {
      connect: vi.fn(),
      gain: {
        setValueAtTime: vi.fn(),
        linearRampToValueAtTime: vi.fn(),
      },
    };

    mockAudioContextInstance = {
      state: 'running',
      currentTime: 0,
      destination: {},
      createOscillator: vi.fn().mockReturnValue(mockOscillator),
      createGain: vi.fn().mockReturnValue(mockGain),
      resume: vi.fn(),
    };

    class MockAudioContext {
      constructor() {
        return mockAudioContextInstance;
      }
    }

    (window as any).AudioContext = MockAudioContext;
  });

  it('initializes audio context and activates audio on toggleAudio', async () => {
    const { isAudioActive, toggleAudio } = usePackingAudio();

    expect(isAudioActive.value).toBe(false);
    toggleAudio();
    expect(isAudioActive.value).toBe(true);
    // Allow promise tick
    await new Promise((r) => setTimeout(r, 10));
    expect(mockAudioContextInstance.createOscillator).toHaveBeenCalled();
  });

  it('plays success sound with sine wave oscillator at 1200Hz', async () => {
    const { initAudio, playSuccessSound } = usePackingAudio();
    await initAudio();
    playSuccessSound();

    expect(mockAudioContextInstance.createOscillator).toHaveBeenCalled();
    expect(mockOscillator.type).toBe('sine');
    expect(mockOscillator.frequency.setValueAtTime).toHaveBeenCalledWith(1200, 0);
    expect(mockOscillator.start).toHaveBeenCalled();
    expect(mockOscillator.stop).toHaveBeenCalled();
  });

  it('plays scan alert with square wave beeps', async () => {
    const { initAudio, playScanAlert } = usePackingAudio();
    await initAudio();
    playScanAlert();

    expect(mockAudioContextInstance.createOscillator).toHaveBeenCalled();
    expect(mockOscillator.type).toBe('square');
    expect(mockOscillator.start).toHaveBeenCalled();
  });
});
