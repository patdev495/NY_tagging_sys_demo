import { watch } from 'vue';

export function usePackingStatePersistence(stateRefs: Record<string, any>) {
  const STORAGE_KEY = 'packingState';

  const saveState = () => {
    const state: Record<string, any> = {};
    for (const [key, refVal] of Object.entries(stateRefs)) {
      state[key] = refVal?.value;
    }
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  };

  const restoreState = () => {
    const saved = sessionStorage.getItem(STORAGE_KEY);
    if (!saved) return false;
    try {
      const state = JSON.parse(saved);
      for (const [key, val] of Object.entries(state)) {
        if (stateRefs[key] !== undefined && val !== undefined) {
          stateRefs[key].value = val;
        }
      }
      return true;
    } catch (e) {
      console.error('Failed to restore packing state from sessionStorage', e);
      return false;
    }
  };

  const initPersistence = () => {
    watch(
      Object.values(stateRefs),
      () => {
        saveState();
      },
      { deep: true }
    );
  };

  return {
    saveState,
    restoreState,
    initPersistence,
  };
}
