import { BrandMark } from "../brand/BrandMark";
import { ThemeToggle } from "../ui/ThemeToggle";

export function TopBar() {
  return (
    <header className="topbar">
      <div className="brand">
        <BrandMark className="w-[26px] h-[26px] text-accent" />
        <div className="brand-name">
          cer<em>e</em>bro
        </div>
      </div>

      <div className="model-bar">
        <span className="model-name">—</span>
        <span className="model-hash">—</span>
      </div>

      <div className="topbar-actions">
        <button className="icon-btn" title="Search" aria-label="Search">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="11" cy="11" r="7" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
        </button>
        <ThemeToggle />
        <button className="btn" disabled>Export</button>
        <button className="btn primary" disabled>Re-extract</button>
      </div>
    </header>
  );
}
