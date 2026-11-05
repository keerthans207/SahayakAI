import { CheckCircle, XCircle, AlertCircle, HelpCircle, ArrowRight } from "lucide-react";
import { useTranslation } from "react-i18next";
import type { EligibilityRead } from "@/types/api";
import { eligibilityColor, eligibilityBg } from "@/lib/statusColors";

interface Props { result: EligibilityRead }

export function EligibilityResult({ result }: Props) {
  const { t } = useTranslation();
  const color = eligibilityColor(result.outcome);
  const bg = eligibilityBg(result.outcome);

  return (
    <div className="flex flex-col gap-4">
      {/* Outcome banner */}
      <div className="flex items-center gap-3 rounded-xl p-4"
           style={{ background: bg, border: `1.5px solid ${color}` }}
           role="status"
           aria-live="polite">
        <div className="h-10 w-10 flex items-center justify-center rounded-full"
             style={{ background: color + "22" }}>
          {result.outcome === "likely_eligible" || result.outcome === "potentially_eligible"
            ? <CheckCircle className="h-6 w-6" style={{ color }} aria-hidden />
            : result.outcome === "not_eligible"
            ? <XCircle className="h-6 w-6" style={{ color }} aria-hidden />
            : <AlertCircle className="h-6 w-6" style={{ color }} aria-hidden />}
        </div>
        <div>
          <p className="font-bold text-base" style={{ color }}>
            {t(`eligibility.outcomes.${result.outcome}`)}
          </p>
          <p className="text-xs mt-0.5" style={{ color: "hsl(var(--color-text-muted))" }}>
            {t("eligibility.outcome_note")}
          </p>
        </div>
      </div>

      {/* Satisfied */}
      {result.requirements_satisfied.length > 0 && (
        <Section title={t("eligibility.satisfied")} icon={<CheckCircle className="h-4 w-4 text-green-600" />}>
          {result.requirements_satisfied.map((r, i) => (
            <RequirementRow key={i} r={r} status="satisfied" />
          ))}
        </Section>
      )}

      {/* Not satisfied */}
      {result.requirements_not_satisfied.length > 0 && (
        <Section title={t("eligibility.not_satisfied")} icon={<XCircle className="h-4 w-4 text-red-500" />}>
          {result.requirements_not_satisfied.map((r, i) => (
            <RequirementRow key={i} r={r} status="not_satisfied" />
          ))}
        </Section>
      )}

      {/* Unknown */}
      {result.unknown_requirements.length > 0 && (
        <Section title={t("eligibility.unknown")} icon={<HelpCircle className="h-4 w-4 text-amber-500" />}>
          {result.unknown_requirements.map((r, i) => (
            <RequirementRow key={i} r={r} status="unknown" />
          ))}
        </Section>
      )}

      {/* Missing info */}
      {result.missing_information.length > 0 && (
        <Section title={t("eligibility.missing_info")} icon={<AlertCircle className="h-4 w-4 text-amber-500" />}>
          {result.missing_information.map((m, i) => (
            <p key={i} className="text-sm" style={{ color: "hsl(var(--color-text))" }}>• {m}</p>
          ))}
        </Section>
      )}

      {/* Next steps */}
      {result.next_steps.length > 0 && (
        <Section title={t("eligibility.next_steps")} icon={<ArrowRight className="h-4 w-4 text-blue-600" />}>
          {result.next_steps.map((s, i) => (
            <p key={i} className="text-sm" style={{ color: "hsl(var(--color-text))" }}>
              {i + 1}. {s}
            </p>
          ))}
        </Section>
      )}
    </div>
  );
}

function Section({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border p-3 flex flex-col gap-2"
         style={{ borderColor: "hsl(var(--color-border))" }}>
      <p className="flex items-center gap-2 text-sm font-semibold"
         style={{ color: "hsl(var(--color-text))" }}>
        {icon}{title}
      </p>
      <div className="flex flex-col gap-1.5 pl-6">{children}</div>
    </div>
  );
}

function RequirementRow({ r, status }: { r: { rule_type: string; detail?: string; description?: string }; status: string }) {
  const color = status === "satisfied" ? "#16a34a" : status === "not_satisfied" ? "#dc2626" : "#d97706";
  return (
    <div className="text-sm">
      <span className="font-medium capitalize" style={{ color }}>
        {r.rule_type.replace(/_/g, " ")}
      </span>
      {(r.detail ?? r.description) && (
        <span style={{ color: "hsl(var(--color-text-muted))" }}> — {r.detail ?? r.description}</span>
      )}
    </div>
  );
}
