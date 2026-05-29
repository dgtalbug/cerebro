import { useMemo } from "react";
import { useTheme } from "./theme";

function cssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

export function useAccentColor(): string {
  const theme = useTheme((s) => s.theme);
  return useMemo(() => cssVar("--accent"), [theme]);
}

export function useHeatmapColors(): [string, string] {
  const theme = useTheme((s) => s.theme);
  return useMemo(() => [cssVar("--bg-elev"), cssVar("--accent")], [theme]);
}
