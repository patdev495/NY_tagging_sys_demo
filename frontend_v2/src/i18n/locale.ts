export const supportedLocales = ['vi', 'en'] as const;

export type SupportedLocale = (typeof supportedLocales)[number];

const displayLocales: Record<SupportedLocale, string> = {
  vi: 'vi-VN',
  en: 'en-US',
};

export function normalizeLocale(value: unknown): SupportedLocale {
  return value === 'en' || value === 'vi' ? value : 'vi';
}

export function displayLocale(locale: unknown): string {
  return displayLocales[normalizeLocale(locale)];
}

export function formatNumber(value: number, locale: unknown, options?: Intl.NumberFormatOptions): string {
  return new Intl.NumberFormat(displayLocale(locale), options).format(value);
}

export function formatDateTime(value: Date | string | number, locale: unknown, options?: Intl.DateTimeFormatOptions): string {
  return new Intl.DateTimeFormat(displayLocale(locale), options).format(new Date(value));
}
