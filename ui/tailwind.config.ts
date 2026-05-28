import type { Config } from "tailwindcss";

/*
 * Tailwind reads from CSS variables (declared in src/styles/tokens.css)
 * so light and dark themes swap by flipping `data-theme` on <html>.
 *
 * Colours use plain `var(--x)` — no `<alpha-value>` syntax, no HSL
 * re-derivation — because the mockup values are hex and the schema
 * freeze says "no re-derivation". The trade-off: bg-accent/50 opacity
 * utilities don't work. If that becomes a need, a parallel --x-hsl
 * layer can be added without changing the canonical hex values.
 */
export default {
  darkMode: ["class", '[data-theme="dark"]'],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Mockup tokens
        bg: "var(--bg)",
        "bg-elev": "var(--bg-elev)",
        "bg-elev-2": "var(--bg-elev-2)",
        "bg-hover": "var(--bg-hover)",
        border: "var(--border)",
        "border-strong": "var(--border-strong)",
        text: "var(--text)",
        "text-muted": "var(--text-muted)",
        "text-dim": "var(--text-dim)",
        accent: "var(--accent)",
        "accent-bright": "var(--accent-bright)",
        "accent-dim": "var(--accent-dim)",
        blue: "var(--blue)",
        green: "var(--green)",
        red: "var(--red)",
        amber: "var(--amber)",
        purple: "var(--purple)",

        // shadcn aliases — shadcn primitives copied later resolve through these.
        background: "var(--background)",
        foreground: "var(--foreground)",
        card: "var(--card)",
        "card-foreground": "var(--card-foreground)",
        popover: "var(--popover)",
        "popover-foreground": "var(--popover-foreground)",
        primary: "var(--primary)",
        "primary-foreground": "var(--primary-foreground)",
        secondary: "var(--secondary)",
        "secondary-foreground": "var(--secondary-foreground)",
        muted: "var(--muted)",
        "muted-foreground": "var(--muted-foreground)",
        "accent-foreground": "var(--accent-foreground)",
        destructive: "var(--destructive)",
        "destructive-foreground": "var(--destructive-foreground)",
        input: "var(--input)",
        ring: "var(--ring)",
      },
      fontFamily: {
        display: ["var(--font-display)"],
        body: ["var(--font-body)"],
        mono: ["var(--font-mono)"],
      },
      borderRadius: {
        DEFAULT: "var(--radius)",
        lg: "var(--radius-lg)",
      },
    },
  },
  plugins: [],
} satisfies Config;
