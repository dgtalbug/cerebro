import type { ReactNode } from "react";

interface ViewHeaderProps {
  title: string;
  titleEmphasis: string;
  subtitle: string;
  children?: ReactNode;
}

export function ViewHeader({ title, titleEmphasis, subtitle, children }: ViewHeaderProps) {
  return (
    <div className="view-header">
      <div>
        <h1 className="view-title">
          {title} <em>{titleEmphasis}</em>
        </h1>
        <p className="view-subtitle">{subtitle}</p>
      </div>
      {children && <div className="view-actions">{children}</div>}
    </div>
  );
}
