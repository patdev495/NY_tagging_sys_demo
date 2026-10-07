import { defineStore } from 'pinia';
import { ref, watch } from 'vue';
import { setLocale } from '../../i18n';
import { normalizeLocale, type SupportedLocale } from '../../i18n/locale';

export const useSettingsStore = defineStore('settings', () => {
  const stationId = ref<string>('');
  const printerName = ref<string>('');
  const templatePath = ref<string>('');
  const audioDeviceId = ref<string>('');
  const printMode = ref<'centralized' | 'local'>('centralized');
  const agentUrl = ref<string>('http://localhost:8080');
  const localTemplateDir = ref<string>('D:\\PAT\\Templates');
  const language = ref<SupportedLocale>('vi');

  function loadSettings() {
    const saved = localStorage.getItem('ny_packing_settings');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed.stationId !== undefined) stationId.value = parsed.stationId;
        if (parsed.printerName !== undefined) printerName.value = parsed.printerName;
        if (parsed.templatePath !== undefined) templatePath.value = parsed.templatePath;
        if (parsed.audioDeviceId !== undefined) audioDeviceId.value = parsed.audioDeviceId;
        if (parsed.printMode !== undefined) printMode.value = parsed.printMode;
        if (parsed.agentUrl !== undefined) agentUrl.value = parsed.agentUrl;
        if (parsed.localTemplateDir !== undefined) {
          localTemplateDir.value = (!parsed.localTemplateDir || parsed.localTemplateDir === 'C:\\NY_Templates\\')
            ? 'D:\\PAT\\Templates'
            : parsed.localTemplateDir;
        }
        language.value = normalizeLocale(parsed.language);
      } catch (e) {
        console.error('Failed to parse settings', e);
      }
    }
    // Sync i18n on load
    setLocale(language.value);
  }

  function saveSettings() {
    const data = {
      stationId: stationId.value,
      printerName: printerName.value,
      templatePath: templatePath.value,
      audioDeviceId: audioDeviceId.value,
      printMode: printMode.value,
      agentUrl: agentUrl.value,
      localTemplateDir: localTemplateDir.value,
      language: language.value,
    };
    localStorage.setItem('ny_packing_settings', JSON.stringify(data));
  }

  function toggleLanguage() {
    language.value = language.value === 'vi' ? 'en' : 'vi';
    saveSettings();
  }

  // Sync i18n when language changes
  watch(language, (newLang) => {
    setLocale(newLang);
  });

  // Auto-load settings on store initialization to prevent race conditions
  loadSettings();

  return {
    stationId,
    printerName,
    templatePath,
    audioDeviceId,
    printMode,
    agentUrl,
    localTemplateDir,
    language,
    toggleLanguage,
    loadSettings,
    saveSettings
  };
});
