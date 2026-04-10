import { createI18n } from "vue-i18n";
import { messages } from "./messages";

export const supportedLocales = ["en", "fr", "de", "lb", "tr", "ar", "he"];
export const rtlLocales = ["ar", "he"];

function normalizeLocale(raw) {
  if (!raw) return "en";
  const l = String(raw).toLowerCase();
  if (l.startsWith("fr")) return "fr";
  if (l.startsWith("de")) return "de";
  if (l.startsWith("tr")) return "tr";
  if (l.startsWith("ar")) return "ar";
  if (l.startsWith("he") || l.startsWith("iw")) return "he";
  if (l.startsWith("lb") || l.startsWith("lu") || l.startsWith("lux")) return "lb";
  return "en";
}

function detectLocale() {
  const stored = localStorage.getItem("pulseid_locale");
  return normalizeLocale(stored || navigator.language || "en");
}

function applyDocumentLocale(locale) {
  const lang = normalizeLocale(locale);
  document.documentElement.lang = lang;
  document.documentElement.dir = rtlLocales.includes(lang) ? "rtl" : "ltr";
}

const initialLocale = detectLocale();

export const i18n = createI18n({
  legacy: false,
  locale: initialLocale,
  fallbackLocale: "en",
  messages,
});

applyDocumentLocale(initialLocale);

export function setLocale(locale) {
  const lang = normalizeLocale(locale);
  i18n.global.locale.value = lang;
  localStorage.setItem("pulseid_locale", lang);
  applyDocumentLocale(lang);
}

export function getCurrentLocale() {
  return normalizeLocale(i18n.global.locale.value);
}
