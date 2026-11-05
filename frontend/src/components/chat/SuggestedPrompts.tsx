import { useTranslation } from "react-i18next";

interface Props {
  onSelect: (prompt: string) => void;
}

export function SuggestedPrompts({ onSelect }: Props) {
  const { t } = useTranslation();
  const prompts = [
    t("chat.prompt1"),
    t("chat.prompt2"),
    t("chat.prompt3"),
    t("chat.prompt4"),
    t("chat.prompt5"),
  ];

  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs font-semibold uppercase tracking-wide text-center"
         style={{ color: "hsl(var(--color-text-subtle))" }}>
        {t("chat.suggested_prompts")}
      </p>
      <div className="flex flex-wrap justify-center gap-2">
        {prompts.map((p, i) => (
          <button
            key={i}
            onClick={() => onSelect(p)}
            className="rounded-full border px-3.5 py-1.5 text-sm transition-colors hover:border-blue-400 hover:text-blue-600"
            style={{
              borderColor: "hsl(var(--color-border))",
              color: "hsl(var(--color-text-muted))",
              background: "hsl(var(--color-surface))",
            }}
          >
            {p}
          </button>
        ))}
      </div>
    </div>
  );
}
