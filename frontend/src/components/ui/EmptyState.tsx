import type { LucideIcon } from "lucide-react";

interface Props {
  icon: LucideIcon;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export function EmptyState({ icon: Icon, title, description, action }: Props) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-dashed p-12 text-center"
         style={{ borderColor: "hsl(var(--color-border))" }}>
      <div className="flex h-14 w-14 items-center justify-center rounded-full"
           style={{ backgroundColor: "hsl(var(--color-surface-2))" }}>
        <Icon className="h-7 w-7" style={{ color: "hsl(var(--color-text-muted))" }} />
      </div>
      <div>
        <p className="font-semibold text-base" style={{ color: "hsl(var(--color-text))" }}>{title}</p>
        {description && (
          <p className="mt-1 text-sm" style={{ color: "hsl(var(--color-text-muted))" }}>{description}</p>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}
