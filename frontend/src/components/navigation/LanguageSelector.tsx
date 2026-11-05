import { useTranslation } from "react-i18next";
import { Languages } from "lucide-react";
import { SUPPORTED_LANGUAGES } from "@/i18n/index";
import { useAppStore } from "@/store/appStore";

export function LanguageSelector() {
  const { i18n } = useTranslation();
  const { language, setLanguage } = useAppStore();

  const handleChange = (code: string) => {
    setLanguage(code);
    i18n.changeLanguage(code);
    // Set RTL if needed.
    const lang = SUPPORTED_LANGUAGES.find((l) => l.code === code);
    document.documentElement.dir = lang?.rtl ? "rtl" : "ltr";
    document.documentElement.lang = code;
  };

  const current = SUPPORTED_LANGUAGES.find((l) => l.code === language);

  return (
    <div className="relative">
      <label className="sr-only" htmlFor="language-select">Select language</label>
      <div className="flex items-center gap-1.5">
        <Languages className="h-4 w-4 shrink-0" style={{ color: "hsl(var(--color-text-muted))" }} aria-hidden />
        <select
          id="language-select"
          value={language}
          onChange={(e) => handleChange(e.target.value)}
          className="cursor-pointer rounded-md border-none bg-transparent py-1 pl-1 pr-6 text-sm font-medium focus-visible:ring-2"
          style={{ color: "hsl(var(--color-text))" }}
          aria-label="Language"
        >
          {SUPPORTED_LANGUAGES.map((l) => (
            <option key={l.code} value={l.code}>
              {l.native}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
