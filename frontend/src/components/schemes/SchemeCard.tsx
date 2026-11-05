import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ExternalLink, ChevronRight, Building2 } from "lucide-react";
import type { SchemeSummary } from "@/types/api";
import { Badge, schemeSatusBadgeVariant } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";

interface Props {
  scheme: SchemeSummary;
}

export function SchemeCard({ scheme }: Props) {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <article
      className="card group flex flex-col gap-3 hover:shadow-md transition-shadow cursor-pointer"
      onClick={() => navigate(`/schemes/${scheme.scheme_id}`)}
      tabIndex={0}
      role="button"
      aria-label={`View details for ${scheme.official_name}`}
      onKeyDown={(e) => e.key === "Enter" && navigate(`/schemes/${scheme.scheme_id}`)}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-2.5 min-w-0">
          <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg"
               style={{ background: "hsl(var(--color-surface-2))" }}>
            <Building2 className="h-5 w-5" style={{ color: "hsl(var(--color-primary))" }} aria-hidden />
          </div>
          <div className="min-w-0">
            <h3 className="text-sm font-semibold leading-tight line-clamp-2"
                style={{ color: "hsl(var(--color-text))" }}>
              {scheme.official_name}
            </h3>
            <p className="mt-0.5 text-xs" style={{ color: "hsl(var(--color-text-muted))" }}>
              {scheme.applicable_state ?? t("schemes.central")} ·{" "}
              {t(`schemes.categories.${scheme.category}` as const, { defaultValue: scheme.category })}
            </p>
          </div>
        </div>
        <ChevronRight className="h-4 w-4 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity"
                      style={{ color: "hsl(var(--color-text-subtle))" }} aria-hidden />
      </div>

      {/* Badges */}
      <div className="flex flex-wrap gap-1.5">
        <Badge variant={schemeSatusBadgeVariant(scheme.scheme_status)}>
          {t(`schemes.${scheme.scheme_status}` as const, { defaultValue: scheme.scheme_status })}
        </Badge>
        <Badge variant={scheme.government_level === "central" ? "info" : "neutral"}>
          {t(`schemes.${scheme.government_level}` as const, { defaultValue: scheme.government_level })}
        </Badge>
        {scheme.confidence_status === "needs_verification" && (
          <Badge variant="warning">{t("common.needs_verification")}</Badge>
        )}
      </div>

      {/* Benefit */}
      {scheme.benefit_amount && (
        <p className="text-xs" style={{ color: "hsl(var(--color-text-muted))" }}>
          {scheme.benefit_amount}
        </p>
      )}

      {/* Actions */}
      <div className="flex gap-2 mt-auto pt-2 border-t" style={{ borderColor: "hsl(var(--color-border))" }}>
        <button
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/eligibility?scheme=${scheme.scheme_id}`);
          }}
          className="btn-primary flex-1 text-xs py-1.5"
          aria-label={`${t("schemes.check_eligibility")} for ${scheme.official_name}`}
        >
          {t("schemes.check_eligibility")}
        </button>
      </div>
    </article>
  );
}
