/**
 * Theme store and switcher.
 *
 * One Zustand store + one `applyTheme` side-effect helper. Reading and
 * mutating theme always goes through `useTheme()`; the helper is
 * exported for tests only. First-load resolution order:
 *
 *   1. `localStorage["cerebro-theme"]` if set to "dark" or "light".
 *   2. `prefers-color-scheme` media query.
 *   3. Hard fall-back to "dark".
 *
 * Storage failures (private-mode browsers, sandboxed iframes) degrade
 * gracefully: the theme still applies for the session, it just won't
 * persist across reloads.
 */

import { create } from "zustand";

export type Theme = "dark" | "light";

const STORAGE_KEY = "cerebro-theme";

interface ThemeStore {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

function isTheme(value: unknown): value is Theme {
  return value === "dark" || value === "light";
}

function readStored(): Theme | null {
  if (typeof window === "undefined") return null;
  try {
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return isTheme(stored) ? stored : null;
  } catch {
    return null;
  }
}

function readSystem(): Theme {
  if (typeof window === "undefined" || !window.matchMedia) return "dark";
  if (window.matchMedia("(prefers-color-scheme: light)").matches) return "light";
  return "dark";
}

export function readInitialTheme(): Theme {
  return readStored() ?? readSystem();
}

export function applyTheme(theme: Theme): void {
  if (typeof document !== "undefined") {
    document.documentElement.setAttribute("data-theme", theme);
  }
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, theme);
  } catch {
    // localStorage unavailable; theme persists for the session only.
  }
}

export const useTheme = create<ThemeStore>((set, get) => {
  const initial = readInitialTheme();
  applyTheme(initial);
  return {
    theme: initial,
    setTheme: (theme) => {
      applyTheme(theme);
      set({ theme });
    },
    toggleTheme: () => {
      const next: Theme = get().theme === "dark" ? "light" : "dark";
      applyTheme(next);
      set({ theme: next });
    },
  };
});
