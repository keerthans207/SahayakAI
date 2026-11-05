import { useTranslation } from "react-i18next";
import { Eye, Type, ZapOff, Sun, Moon, Monitor } from "lucide-react";
import { useAppStore, type FontSize, type Theme } from "@/store/appStore";

export function AccessibilityToolbar() {
  const { t } = useTranslation();
  const { fontSize, setFontSize, reduceMotion, setReduceMotion, highContrast, setHighContrast, theme, setTheme } = useAppStore();

  const fontSizes: { label: string; value: FontSize }[] = [
    { label: "A", value: "sm" },
    { label: "A", value: "md" },
    { label: "A", value: "lg" },
    { label: "A", value: "xl" },
  ];
  const fontSizeScale = { sm: "0.75rem", md: "0.875rem", lg: "1rem", xl: "1.1rem" };

  return (
    <div
      className="flex items-center gap-3 rounded-lg border p-2"
      style={{ borderColor: "hsl(var(--color-border))", background: "hsl(var(--color-surface))" }}
      role="group"
      aria-label={t("settings.accessibility")}
    >
      {/* Font size */}
      <div className="flex items-center gap-0.5" role="group" aria-label={t("settings.font_size")}>
        {fontSizes.map(({ label, value }) => (
          <button
            key={value}
            onClick={() => setFontSize(value)}
            className="flex h-7 w-7 items-center justify-center rounded font-bold transition-colors"
            style={{
              fontSize: fontSizeScale[value],
              background: fontSize === value ? "hsl(var(--color-primary))" : "transparent",
              color: fontSize === value ? "#fff" : "hsl(var(--color-text-muted))",
            }}
            aria-pressed={fontSize === value}
            aria-label={`Font size ${value}`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="h-4 w-px" style={{ background: "hsl(var(--color-border))" }} />

      {/* Theme */}
      <div className="flex items-center gap-0.5" role="group" aria-label={t("settings.theme")}>
        {([["light", Sun], ["system", Monitor], ["dark", Moon]] as [Theme, typeof Sun][]).map(([t_val, Icon]) => (
          <button
            key={t_val}
            onClick={() => setTheme(t_val)}
            className="flex h-7 w-7 items-center justify-center rounded transition-colors"
            style={{
              background: theme === t_val ? "hsl(var(--color-primary))" : "transparent",
              color: theme === t_val ? "#fff" : "hsl(var(--color-text-muted))",
            }}
            aria-pressed={theme === t_val}
            aria-label={`${t_val} mode`}
          >
            <Icon className="h-3.5 w-3.5" aria-hidden />
          </button>
        ))}
      </div>

      <div className="h-4 w-px" style={{ background: "hsl(var(--color-border))" }} />

      {/* High contrast */}
      <button
        onClick={() => setHighContrast(!highContrast)}
        className="flex h-7 w-7 items-center justify-center rounded transition-colors"
        style={{
          background: highContrast ? "hsl(var(--color-primary))" : "transparent",
          color: highContrast ? "#fff" : "hsl(var(--color-text-muted))",
        }}
        aria-pressed={highContrast}
        aria-label={t("settings.high_contrast")}
        title={t("settings.high_contrast")}
      >
        <Eye className="h-3.5 w-3.5" aria-hidden />
      </button>

      {/* Reduce motion */}
      <button
        onClick={() => setReduceMotion(!reduceMotion)}
        className="flex h-7 w-7 items-center justify-center rounded transition-colors"
        style={{
          background: reduceMotion ? "hsl(var(--color-primary))" : "transparent",
          color: reduceMotion ? "#fff" : "hsl(var(--color-text-muted))",
        }}
        aria-pressed={reduceMotion}
        aria-label={t("settings.reduce_motion")}
        title={t("settings.reduce_motion")}
      >
        <ZapOff className="h-3.5 w-3.5" aria-hidden />
      </button>
    </div>
  );
}
