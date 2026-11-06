import { ExternalLink, AlertCircle } from "lucide-react";
import { useTranslation } from "react-i18next";
import type { OfficialSource } from "@/types/api";

interface Props {
  sources: OfficialSource[];
}

export function SourceCitation({ sources }: Props) {
  const { t } = useTranslation();
  if (!sources.length) return null;

  return (
    <div className="mt-3 rounded-lg border p-3"
         style={{ borderColor: "hsl(var(--color-border))", background: "hsl(var(--color-surface-2))" }}>
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide"
         style={{ color: "hsl(var(--color-text-muted))" }}>
        {t("chat.sources")}
      </p>
      <ul className="space-y-1.5 list-none p-0 m-0">
        {sources.map((s, i) => (
          <li key={i} className="flex items-start gap-2">
            {s.source_status === "official" ? (
              <span className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-green-500" aria-hidden title="Official source" />
            ) : (
              <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-amber-500" aria-hidden aria-label="Needs verification" />
            )}
            <div className="min-w-0">
              {s.url ? (
                <a
                  href={s.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline truncate"
                  aria-label={`${s.title ?? "Source"} (opens in new tab)`}
                >
                  {s.title ?? s.url}
                  <ExternalLink className="h-3 w-3 shrink-0" aria-hidden />
                </a>
              ) : (
                <span className="text-xs" style={{ color: "hsl(var(--color-text-muted))" }}>
                  {s.title ?? t("common.official_source")}
                </span>
              )}
              {s.publisher && (
                <span className="ml-1 text-xs" style={{ color: "hsl(var(--color-text-subtle))" }}>
                  · {s.publisher}
                </span>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
