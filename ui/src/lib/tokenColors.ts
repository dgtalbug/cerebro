import { useMemo } from "react";
import { useTheme } from "./theme";

function cssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

export function useAccentColor(): string {
  useTheme((s) => s.theme);
  return useMemo(() => cssVar("--accent"), []);
}

export function useHeatmapColors(): [string, string] {
  useTheme((s) => s.theme);
  return useMemo(() => [cssVar("--bg-elev"), cssVar("--accent")], []);
}
