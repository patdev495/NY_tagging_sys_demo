import { createI18n } from 'vue-i18n';
import en from './locales/en';
import vi from './locales/vi';
import type { SupportedLocale } from './locale';

// Define messages
const messages = {
  en,
  vi
};

// Create i18n instance
const i18n = createI18n({
  legacy: false, // Use Composition API
  locale: 'vi', // Default locale
  fallbackLocale: 'en', // Fallback locale
  messages,
});

export function setLocale(locale: SupportedLocale) {
  i18n.global.locale.value = locale;
}

export default i18n;
