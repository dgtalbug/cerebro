import { NavLink, useLocation, useNavigate, useParams } from "react-router-dom";
import {
  LayoutGrid,
  GitBranch,
  BarChart2,
  Database,
  HelpCircle,
  ClipboardCheck,
  MessageSquare,
  BadgeCheck,
  FileCode,
  Monitor,
  AlignJustify,
  Plus,
  ChevronLeft,
  Code,
} from "lucide-react";
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
    icon: <LayoutGrid size={14} strokeWidth={1.5} />,
  },
  {
    label: "Trees",
    view: "trees",
    disabled: false,
    icon: <GitBranch size={14} strokeWidth={1.5} />,
  },
  {
    label: "Importance",
    view: "importance",
    disabled: false,
    icon: <BarChart2 size={14} strokeWidth={1.5} />,
  },
  {
    label: "Data",
    view: "data",
    disabled: false,
    icon: <Database size={14} strokeWidth={1.5} />,
  },
  {
    label: "Explanations",
    view: "explanations",
    disabled: false,
    icon: <HelpCircle size={14} strokeWidth={1.5} />,
  },
  {
    label: "Evaluation",
    view: "evaluation",
    disabled: false,
    icon: <ClipboardCheck size={14} strokeWidth={1.5} />,
  },
];


const reasoningItems: NavItemDef[] = [
  {
    label: "Agent",
    view: "agent",
    disabled: false,
    icon: <MessageSquare size={14} strokeWidth={1.5} />,
  },
];

const artifactItems: NavItemDef[] = [
  {
    label: "Readiness",
    view: "readiness",
    disabled: false,
    icon: <BadgeCheck size={14} strokeWidth={1.5} />,
  },
  {
    label: "Schema / JSON",
    view: "schema",
    disabled: true,
    icon: <FileCode size={14} strokeWidth={1.5} />,
  },
  {
    label: "Code Guide",
    view: "code-guide",
    disabled: false,
    icon: <Code size={14} strokeWidth={1.5} />,
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

function RegistrySidebarNav() {
  const navigate = useNavigate();
  return (
    <>
      <NavLink
        to="/"
        end
        className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
      >
        <Monitor size={14} strokeWidth={1.5} />
        <span>Registry</span>
      </NavLink>
      <NavLink
        to="/artifacts"
        className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
      >
        <AlignJustify size={14} strokeWidth={1.5} />
        <span>Artifacts</span>
      </NavLink>
      <button
        className="btn primary"
        onClick={() => navigate("/ingest")}
        style={{ width: "100%", justifyContent: "center", marginTop: "16px", gap: "8px" }}
      >
        <Plus size={12} strokeWidth={2.5} />
        Load model
      </button>
    </>
  );
}

export function Sidebar() {
  const { id } = useParams<{ id?: string }>();
  const location = useLocation();
  const { data } = useArtifact(id ?? "");
  const artifact = id ? data?.data : undefined;
  const navigate = useNavigate();

  const isArtifactRoute = location.pathname.startsWith("/artifacts/");

  const extractedAt = artifact
    ? artifact.source.extracted_at.replace("T", " ").replace("Z", " UTC")
    : "—";
  const extractorVer = artifact ? artifact.source.extractor_version : "—";

  if (!isArtifactRoute) {
    return (
      <aside className="sidebar">
        <RegistrySidebarNav />
      </aside>
    );
  }

  return (
    <aside className="sidebar">
      <NavLink
        to="/"
        className="nav-item"
        style={{ marginBottom: "8px", fontSize: "11px", color: "var(--text-dim)" }}
      >
        <ChevronLeft size={14} strokeWidth={1.5} />
        <span>Registry</span>
      </NavLink>
      <button
        className="btn primary"
        onClick={() => navigate("/ingest")}
        style={{ width: "100%", justifyContent: "center", marginBottom: "20px", gap: "8px" }}
      >
        <Plus size={12} strokeWidth={2.5} />
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
