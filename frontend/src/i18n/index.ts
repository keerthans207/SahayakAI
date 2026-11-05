import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./locales/en";
import kn from "./locales/kn";

// Additional languages are structured but not yet translated — they fall back to English.
export const SUPPORTED_LANGUAGES = [
  { code: "en", name: "English", native: "English", rtl: false },
  { code: "kn", name: "Kannada", native: "ಕನ್ನಡ", rtl: false },
  { code: "hi", name: "Hindi", native: "हिंदी", rtl: false },
  { code: "ta", name: "Tamil", native: "தமிழ்", rtl: false },
  { code: "te", name: "Telugu", native: "తెలుగు", rtl: false },
  { code: "ml", name: "Malayalam", native: "മലയാളം", rtl: false },
  { code: "mr", name: "Marathi", native: "मराठी", rtl: false },
  { code: "bn", name: "Bengali", native: "বাংলা", rtl: false },
  { code: "gu", name: "Gujarati", native: "ગુજરાતી", rtl: false },
  { code: "pa", name: "Punjabi", native: "ਪੰਜਾਬੀ", rtl: false },
  { code: "or", name: "Odia", native: "ଓଡ଼ିଆ", rtl: false },
  { code: "as", name: "Assamese", native: "অসমীয়া", rtl: false },
  { code: "ur", name: "Urdu", native: "اردو", rtl: true },
] as const;

export type LanguageCode = (typeof SUPPORTED_LANGUAGES)[number]["code"];

i18n.use(initReactI18next).init({
  resources: { en: { translation: en }, kn: { translation: kn } },
  lng: localStorage.getItem("sahayak-preferences")
    ? (JSON.parse(localStorage.getItem("sahayak-preferences")!).state?.language ?? "en")
    : "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

export default i18n;
