import { NavLink } from "react-router-dom";

interface NavItemDef {
  label: string;
  view: string;
  icon: JSX.Element;
  disabled?: boolean;
  count?: string;
}

const introspectionItems: NavItemDef[] = [
  {
    label: "Overview",
    view: "overview",
    disabled: false,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <rect x="3" y="3" width="7" height="7" /><rect x="14" y="3" width="7" height="7" />
        <rect x="14" y="14" width="7" height="7" /><rect x="3" y="14" width="7" height="7" />
      </svg>
    ),
  },
  {
    label: "Trees",
    view: "trees",
    disabled: true,
    count: "—",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M12 3v18M5 8l7-5 7 5M5 16l7-5 7 5" />
      </svg>
    ),
  },
  {
    label: "Importance",
    view: "importance",
    disabled: true,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M3 21v-4M9 21v-9M15 21v-14M21 21v-6" />
      </svg>
    ),
  },
  {
    label: "Explanations",
    view: "explanations",
    disabled: true,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <circle cx="12" cy="12" r="9" /><path d="M9 9a3 3 0 015.83 1c0 2-3 3-3 3M12 17v.01" />
      </svg>
    ),
  },
  {
    label: "Evaluation",
    view: "evaluation",
    disabled: true,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M3 12l5 5L21 4" />
      </svg>
    ),
  },
];

const reasoningItems: NavItemDef[] = [
  {
    label: "Agent",
    view: "agent",
    disabled: true,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
      </svg>
    ),
  },
];

const artifactItems: NavItemDef[] = [
  {
    label: "Schema / JSON",
    view: "schema",
    disabled: true,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
        <polyline points="14 2 14 8 20 8" />
      </svg>
    ),
  },
];

function NavItem({ item }: { item: NavItemDef }) {
  const to = `/artifacts/:id/${item.view}`;

  if (item.disabled) {
    return (
      <div className="nav-item opacity-40 select-none pointer-events-none">
        {item.icon}
        <span>{item.label}</span>
        {item.count && <span className="nav-count">{item.count}</span>}
      </div>
    );
  }

  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `nav-item ${isActive ? "active" : ""}`
      }
    >
      {item.icon}
      <span>{item.label}</span>
      {item.count && <span className="nav-count">{item.count}</span>}
    </NavLink>
  );
}

function NavSection({ label, items }: { label: string; items: NavItemDef[] }) {
  return (
    <div className="nav-section">
      <div className="nav-label">{label}</div>
      {items.map((item) => (
        <NavItem key={item.view} item={item} />
      ))}
    </div>
  );
}

export function Sidebar() {
  return (
    <aside className="sidebar">
      <NavSection label="Introspection" items={introspectionItems} />
      <NavSection label="Reasoning" items={reasoningItems} />
      <NavSection label="Artifact" items={artifactItems} />

      <div className="sidebar-footer">
        <div><span className="footer-label">extracted</span> —</div>
        <div><span className="footer-label">size</span> —</div>
        <div><span className="footer-label">extractor</span> —</div>
      </div>
    </aside>
  );
}
