import { ref } from 'vue';

export interface UsePackingAudioOptions {
  audioDeviceId?: string;
}

export function usePackingAudio(options: UsePackingAudioOptions = {}) {
  const isAudioActive = ref<boolean>(false);
  let audioCtx: AudioContext | null = null;
  let isAudioInitialized = false;

  const initAudio = async () => {
    if (isAudioInitialized && audioCtx) return;
    try {
      const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
      if (!AudioContextClass) return;

      audioCtx = new AudioContextClass();
      if (options.audioDeviceId && (audioCtx as any).setSinkId) {
        try {
          await (audioCtx as any).setSinkId(options.audioDeviceId);
        } catch {}
      }
      isAudioInitialized = true;
    } catch (e) {
      console.warn('Init AudioContext notice:', e);
    }
  };

  const playSuccessSound = () => {
    try {
      if (!audioCtx) return;
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }
      const o = audioCtx.createOscillator();
      const g = audioCtx.createGain();
      o.connect(g);
      g.connect(audioCtx.destination);
      o.type = 'sine';
      o.frequency.setValueAtTime(1200, audioCtx.currentTime);
      g.gain.setValueAtTime(0, audioCtx.currentTime);
      g.gain.linearRampToValueAtTime(0.5, audioCtx.currentTime + 0.01);
      g.gain.linearRampToValueAtTime(0, audioCtx.currentTime + 0.15);
      o.start(audioCtx.currentTime);
      o.stop(audioCtx.currentTime + 0.15);
    } catch (e) {
      console.warn('Audio success sound failed:', e);
    }
  };

  const playScanAlert = () => {
    try {
      if (!audioCtx) return;
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }

      const beep = (freq: number, start: number, dur: number) => {
        if (!audioCtx) return;
        const o = audioCtx.createOscillator();
        const g = audioCtx.createGain();
        o.connect(g);
        g.connect(audioCtx.destination);
        o.type = 'square';
        o.frequency.setValueAtTime(freq, audioCtx.currentTime + start);

        g.gain.setValueAtTime(0, audioCtx.currentTime + start);
        g.gain.linearRampToValueAtTime(1.0, audioCtx.currentTime + start + 0.005);
        g.gain.linearRampToValueAtTime(0, audioCtx.currentTime + start + dur);

        o.start(audioCtx.currentTime + start);
        o.stop(audioCtx.currentTime + start + dur);
      };

      beep(800, 0, 0.4);
      beep(800, 0.5, 0.4);
      beep(800, 1.0, 0.4);
    } catch (e) {
      console.warn('Audio alert failed:', e);
    }
  };

  const toggleAudio = () => {
    isAudioActive.value = true;
    initAudio().then(playScanAlert);
  };

  return {
    isAudioActive,
    initAudio,
    playSuccessSound,
    playScanAlert,
    toggleAudio,
  };
}
