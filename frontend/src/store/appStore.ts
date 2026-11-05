/**
 * Global client-side state via Zustand.
 * Only non-sensitive preferences are persisted to localStorage.
 * Never store tokens, documents, or Aadhaar data here.
 */
import { create } from "zustand";
import { persist } from "zustand/middleware";

export type FontSize = "sm" | "md" | "lg" | "xl";
export type Theme = "light" | "dark" | "system";

interface AppState {
  // Language
  language: string;
  setLanguage: (lang: string) => void;

  // Accessibility
  fontSize: FontSize;
  setFontSize: (size: FontSize) => void;
  reduceMotion: boolean;
  setReduceMotion: (v: boolean) => void;
  highContrast: boolean;
  setHighContrast: (v: boolean) => void;
  theme: Theme;
  setTheme: (t: Theme) => void;

  // Sidebar
  sidebarOpen: boolean;
  setSidebarOpen: (v: boolean) => void;

  // Active chat session
  activeChatSessionId: string | null;
  setActiveChatSessionId: (id: string | null) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      language: "en",
      setLanguage: (language) => set({ language }),

      fontSize: "md",
      setFontSize: (fontSize) => set({ fontSize }),
      reduceMotion: false,
      setReduceMotion: (reduceMotion) => set({ reduceMotion }),
      highContrast: false,
      setHighContrast: (highContrast) => set({ highContrast }),
      theme: "system",
      setTheme: (theme) => set({ theme }),

      sidebarOpen: true,
      setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),

      activeChatSessionId: null,
      setActiveChatSessionId: (activeChatSessionId) => set({ activeChatSessionId }),
    }),
    {
      name: "sahayak-preferences",
      // Only persist safe preference fields
      partialize: (s) => ({
        language: s.language,
        fontSize: s.fontSize,
        reduceMotion: s.reduceMotion,
        highContrast: s.highContrast,
        theme: s.theme,
        activeChatSessionId: s.activeChatSessionId,
      }),
    }
  )
);
