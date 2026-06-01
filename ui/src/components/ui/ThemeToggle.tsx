import { Moon, Sun } from "lucide-react";
import { useTheme } from "../../lib/theme";

export function ThemeToggle() {
  const theme = useTheme((s) => s.theme);
  const toggleTheme = useTheme((s) => s.toggleTheme);
  const nextLabel = theme === "dark" ? "Switch to light theme" : "Switch to dark theme";

  return (
    <button
      className="icon-btn"
      onClick={toggleTheme}
      title={nextLabel}
      aria-label={nextLabel}
    >
      {theme === "dark" ? (
        <Moon size={14} strokeWidth={1.8} />
      ) : (
        <Sun size={14} strokeWidth={1.8} />
      )}
    </button>
  );
}
