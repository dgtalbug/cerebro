export function BrandMark({ className = "" }: { className?: string }) {
  return (
    <div className={`brand-mark ${className}`}>
      <svg viewBox="0 0 28 28" fill="none" className="w-full h-full">
        {/* Outer hex ring */}
        <circle cx="14" cy="14" r="13" stroke="currentColor" strokeWidth="0.5" opacity="0.25" />
        {/* Node cluster — neural / cerebral motif */}
        <circle cx="14" cy="14" r="2.5" fill="currentColor" />
        <circle cx="7"  cy="10" r="1.5" fill="currentColor" opacity="0.7" />
        <circle cx="21" cy="10" r="1.5" fill="currentColor" opacity="0.7" />
        <circle cx="7"  cy="18" r="1.5" fill="currentColor" opacity="0.7" />
        <circle cx="21" cy="18" r="1.5" fill="currentColor" opacity="0.7" />
        <circle cx="14" cy="5"  r="1.2" fill="currentColor" opacity="0.5" />
        <circle cx="14" cy="23" r="1.2" fill="currentColor" opacity="0.5" />
        {/* Edges */}
        <line x1="14" y1="14" x2="7"  y2="10" stroke="currentColor" strokeWidth="0.7" opacity="0.45" />
        <line x1="14" y1="14" x2="21" y2="10" stroke="currentColor" strokeWidth="0.7" opacity="0.45" />
        <line x1="14" y1="14" x2="7"  y2="18" stroke="currentColor" strokeWidth="0.7" opacity="0.45" />
        <line x1="14" y1="14" x2="21" y2="18" stroke="currentColor" strokeWidth="0.7" opacity="0.45" />
        <line x1="14" y1="14" x2="14" y2="5"  stroke="currentColor" strokeWidth="0.7" opacity="0.35" />
        <line x1="14" y1="14" x2="14" y2="23" stroke="currentColor" strokeWidth="0.7" opacity="0.35" />
        <line x1="7"  y1="10" x2="7"  y2="18" stroke="currentColor" strokeWidth="0.5" opacity="0.25" />
        <line x1="21" y1="10" x2="21" y2="18" stroke="currentColor" strokeWidth="0.5" opacity="0.25" />
        <line x1="7"  y1="10" x2="14" y2="5"  stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
        <line x1="21" y1="10" x2="14" y2="5"  stroke="currentColor" strokeWidth="0.5" opacity="0.2" />
      </svg>
    </div>
  );
}
