import { NavLink, useNavigate, useParams } from "react-router-dom";
import { useArtifact } from "../../lib/api/queries";

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
    disabled: false,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M12 3v18M5 8l7-5 7 5M5 16l7-5 7 5" />
      </svg>
    ),
  },
  {
    label: "Importance",
    view: "importance",
    disabled: false,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <path d="M3 21v-4M9 21v-9M15 21v-14M21 21v-6" />
      </svg>
    ),
  },
  {
    label: "Data",
    view: "data",
    disabled: false,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <ellipse cx="12" cy="5" rx="9" ry="3" />
        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
      </svg>
    ),
  },
  {
    label: "Explanations",
    view: "explanations",
    disabled: false,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
        <circle cx="12" cy="12" r="9" /><path d="M9 9a3 3 0 015.83 1c0 2-3 3-3 3M12 17v.01" />
      </svg>
    ),
  },
  {
    label: "Evaluation",
    view: "evaluation",
    disabled: false,
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
  const { id } = useParams<{ id?: string }>();
  const to = `/artifacts/${id ?? ":id"}/${item.view}`;

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
  const { id } = useParams<{ id?: string }>();
  const { data } = useArtifact(id ?? "");
  const artifact = id ? data?.data : undefined;
  const navigate = useNavigate();

  const extractedAt = artifact
    ? artifact.source.extracted_at.replace("T", " ").replace("Z", " UTC")
    : "—";
  const extractorVer = artifact ? artifact.source.extractor_version : "—";

  return (
    <aside className="sidebar">
      <button
        className="btn primary"
        onClick={() => navigate("/ingest")}
        style={{ width: "100%", justifyContent: "center", marginBottom: "20px", gap: "8px" }}
      >
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
        </svg>
        Load model
      </button>
      <NavSection label="Introspection" items={introspectionItems} />
      <NavSection label="Reasoning" items={reasoningItems} />
      <NavSection label="Artifact" items={artifactItems} />

      <div className="sidebar-footer">
        <div><span className="footer-label">extracted</span> {extractedAt}</div>
        <div><span className="footer-label">size</span> —</div>
        <div><span className="footer-label">extractor</span> {extractorVer}</div>
      </div>
    </aside>
  );
}
