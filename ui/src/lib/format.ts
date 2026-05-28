// Number formatting helpers (Part III: tabular numerals across data views).

/** Format an integer with thousands separators (e.g. 187 -> "187", 1234 -> "1,234"). */
export function formatCount(value: number): string {
  return new Intl.NumberFormat("en-US").format(Math.trunc(value));
}

/** Format a fraction as a fixed-precision percentage (e.g. 0.1234 -> "12.3%"). */
export function formatPercent(fraction: number, digits = 1): string {
  return `${(fraction * 100).toFixed(digits)}%`;
}
