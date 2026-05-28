export function BrandMark({ className = "" }: { className?: string }) {
  return (
    <div className={`brand-mark ${className}`}>
      <svg viewBox="0 0 26 26" fill="none" className="w-full h-full">
        <circle cx="13" cy="13" r="12" stroke="currentColor" strokeWidth="0.6" opacity="0.4" />
        <circle cx="13" cy="13" r="8.5" stroke="currentColor" strokeWidth="0.7" opacity="0.7" />
        <circle cx="13" cy="13" r="5" stroke="currentColor" strokeWidth="0.9" />
        <circle cx="13" cy="13" r="2" fill="currentColor" />
        <line x1="13" y1="0" x2="13" y2="3" stroke="currentColor" strokeWidth="0.6" opacity="0.5" />
        <line x1="13" y1="23" x2="13" y2="26" stroke="currentColor" strokeWidth="0.6" opacity="0.5" />
        <line x1="0" y1="13" x2="3" y2="13" stroke="currentColor" strokeWidth="0.6" opacity="0.5" />
        <line x1="23" y1="13" x2="26" y2="13" stroke="currentColor" strokeWidth="0.6" opacity="0.5" />
      </svg>
    </div>
  );
}
