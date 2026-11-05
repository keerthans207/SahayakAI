import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { LayoutDashboard, Bot, Search, ClipboardList, User } from "lucide-react";
import { cn } from "@/lib/utils";

const MOBILE_NAV = [
  { key: "overview", to: "/dashboard", icon: LayoutDashboard },
  { key: "assistant", to: "/assistant", icon: Bot },
  { key: "discover", to: "/schemes", icon: Search },
  { key: "applications", to: "/applications", icon: ClipboardList },
  { key: "profile", to: "/profile", icon: User },
] as const;

export function MobileNav() {
  const { t } = useTranslation();
  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 flex border-t"
      style={{
        background: "hsl(var(--color-surface))",
        borderColor: "hsl(var(--color-border))",
      }}
      aria-label="Mobile navigation"
    >
      {MOBILE_NAV.map(({ key, to, icon: Icon }) => (
        <NavLink
          key={key}
          to={to}
          className={({ isActive }) =>
            cn(
              "flex flex-1 flex-col items-center gap-0.5 py-3 text-[10px] font-medium transition-colors",
              isActive
                ? "text-blue-600"
                : "text-gray-500 hover:text-gray-800"
            )
          }
          aria-label={t(`nav.${key}`)}
        >
          <Icon className="h-5 w-5" aria-hidden />
          <span className="hidden sm:block">{t(`nav.${key}`)}</span>
        </NavLink>
      ))}
    </nav>
  );
}
