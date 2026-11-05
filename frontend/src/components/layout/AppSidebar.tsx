import { NavLink } from "react-router-dom";
import { useTranslation } from "react-i18next";
import {
  LayoutDashboard, Bot, Search, CheckCircle, FileText, ClipboardList, User, Settings, ChevronLeft, ChevronRight, Heart
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAppStore } from "@/store/appStore";

const NAV_ITEMS = [
  { key: "overview", to: "/dashboard", icon: LayoutDashboard },
  { key: "assistant", to: "/assistant", icon: Bot },
  { key: "discover", to: "/schemes", icon: Search },
  { key: "eligibility", to: "/eligibility", icon: CheckCircle },
  { key: "documents", to: "/documents", icon: FileText },
  { key: "applications", to: "/applications", icon: ClipboardList },
  { key: "profile", to: "/profile", icon: User },
  { key: "settings", to: "/settings", icon: Settings },
] as const;

export function AppSidebar() {
  const { t } = useTranslation();
  const { sidebarOpen, setSidebarOpen } = useAppStore();

  return (
    <aside
      className={cn(
        "flex h-screen flex-col transition-all duration-250",
        sidebarOpen ? "w-60" : "w-16"
      )}
      style={{ background: "hsl(var(--color-sidebar))", color: "hsl(var(--color-sidebar-fg))" }}
      aria-label="Main navigation"
    >
      {/* Logo */}
      <div className="flex h-16 items-center gap-3 px-4 border-b border-white/10">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-500">
          <Heart className="h-4 w-4 text-white" aria-hidden />
        </div>
        {sidebarOpen && (
          <span className="font-bold text-white text-base truncate">Sahayak AI</span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-4 px-2" role="navigation">
        <ul className="space-y-1 list-none p-0 m-0">
          {NAV_ITEMS.map(({ key, to, icon: Icon }) => (
            <li key={key}>
              <NavLink
                to={to}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-600 text-white"
                      : "text-blue-100 hover:bg-white/10 hover:text-white"
                  )
                }
                aria-label={sidebarOpen ? undefined : t(`nav.${key}`)}
                title={!sidebarOpen ? t(`nav.${key}`) : undefined}
              >
                <Icon className="h-5 w-5 shrink-0" aria-hidden />
                {sidebarOpen && <span>{t(`nav.${key}`)}</span>}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      {/* Collapse toggle */}
      <div className="border-t border-white/10 p-2">
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="flex w-full items-center justify-center rounded-lg p-2 text-blue-200 transition-colors hover:bg-white/10 hover:text-white"
          aria-label={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
        >
          {sidebarOpen ? (
            <><ChevronLeft className="h-4 w-4" aria-hidden /><span className="ml-2 text-sm">Collapse</span></>
          ) : (
            <ChevronRight className="h-4 w-4" aria-hidden />
          )}
        </button>
      </div>
    </aside>
  );
}
