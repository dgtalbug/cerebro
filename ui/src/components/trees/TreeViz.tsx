import { Suspense, lazy, useMemo, useRef, useState, useEffect, useCallback } from "react";
import type { RawNodeDatum, CustomNodeElementProps } from "react-d3-tree";
import type { ComponentType } from "react";

const Tree = lazy(() =>
  import("react-d3-tree").then(
    (m) => ({ default: m.default as unknown as ComponentType<Record<string, unknown>> }),
  ),
);

interface CanonicalNode {
  id: number;
  split_feature: number | null;
  threshold: number | null;
  decision_type: string | null;
  left: CanonicalNode | null;
  right: CanonicalNode | null;
  leaf_value: number | null;
}

interface CanonicalTree {
  index: number;
  class_index: number | null;
  num_leaves: number;
  root: CanonicalNode;
}

interface SelectedNode {
  id: number;
  split_feature: number | null;
  threshold: number | null;
  decision_type: string | null;
  leaf_value: number | null;
}

interface HoverState {
  datum: RawNodeDatum;
  x: number; // container-relative px
  y: number;
}

interface Props {
  tree: CanonicalTree;
  featureNames: string[];
  maxDepth?: number;
  onNodeClick: (node: SelectedNode) => void;
}

function toD3Node(
  node: CanonicalNode,
  featureNames: string[],
  depth: number,
  maxDepth: number,
): RawNodeDatum {
  if (depth > maxDepth) {
    return { name: "…", attributes: { truncated: "true" } };
  }
  if (node.left === null && node.right === null) {
    return {
      name: "leaf",
      attributes: {
        value: node.leaf_value !== null ? node.leaf_value.toFixed(4) : "?",
        id: String(node.id),
      },
    };
  }
  const featName =
    node.split_feature !== null
      ? (featureNames[node.split_feature] ?? `f${node.split_feature}`)
      : "?";
  const label = `${featName} ${node.decision_type ?? "<="} ${node.threshold?.toFixed(3) ?? "?"}`;
  const children: RawNodeDatum[] = [];
  if (node.left) children.push(toD3Node(node.left, featureNames, depth + 1, maxDepth));
  if (node.right) children.push(toD3Node(node.right, featureNames, depth + 1, maxDepth));
  return {
    name: label,
    attributes: { id: String(node.id), feat: String(node.split_feature) },
    children,
  };
}

function flattenNodes(node: CanonicalNode): CanonicalNode[] {
  const result: CanonicalNode[] = [node];
  if (node.left) result.push(...flattenNodes(node.left));
  if (node.right) result.push(...flattenNodes(node.right));
  return result;
}

function NodeTooltip({ hover }: { hover: HoverState }) {
  const d = hover.datum;
  const isLeaf = d.name === "leaf";
  const isTruncated = d.attributes?.truncated === "true";

  if (isTruncated) return null;

  return (
    <div
      style={{
        position: "absolute",
        left: hover.x + 14,
        top: hover.y - 8,
        pointerEvents: "none",
        zIndex: 100,
        background: "var(--bg-elev-2)",
        border: "1px solid var(--border)",
        borderRadius: "6px",
        padding: "6px 10px",
        fontSize: "11px",
        fontFamily: "var(--font-mono)",
        color: "var(--text)",
        whiteSpace: "nowrap",
        boxShadow: "0 4px 12px rgba(0,0,0,0.3)",
        maxWidth: "280px",
        lineHeight: "1.5",
      }}
    >
      {isLeaf ? (
        <>
          <span style={{ color: "var(--text-dim)", fontSize: "10px" }}>leaf value</span>
          <br />
          <span style={{ color: "var(--green)", fontWeight: 600 }}>
            {d.attributes?.value ?? "?"}
          </span>
        </>
      ) : (
        <>
          <span style={{ color: "var(--text-dim)", fontSize: "10px" }}>split condition</span>
          <br />
          <span style={{ color: "var(--accent)" }}>{d.name}</span>
        </>
      )}
    </div>
  );
}

function makeCustomNode(
  containerRef: React.RefObject<HTMLDivElement | null>,
  setHover: React.Dispatch<React.SetStateAction<HoverState | null>>,
) {
  return function CustomNode({ nodeDatum }: CustomNodeElementProps) {
    const isLeaf = nodeDatum.name === "leaf";
    const isTruncated = nodeDatum.attributes?.truncated === "true";

    const handleMouseEnter = (e: React.MouseEvent<SVGGElement>) => {
      if (isTruncated || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      setHover({
        datum: nodeDatum,
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      });
    };

    const handleMouseMove = (e: React.MouseEvent<SVGGElement>) => {
      if (isTruncated || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      setHover((prev) =>
        prev ? { ...prev, x: e.clientX - rect.left, y: e.clientY - rect.top } : prev,
      );
    };

    return (
      <g
        style={{ cursor: isTruncated ? "default" : "pointer" }}
        onMouseEnter={handleMouseEnter}
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setHover(null)}
      >
        {/* Invisible hit area for easier hover */}
        <circle r={isTruncated ? 6 : isLeaf ? 14 : 18} fill="transparent" />
        <circle
          r={isTruncated ? 4 : isLeaf ? 5 : 9}
          fill={isTruncated ? "var(--border)" : isLeaf ? "var(--text-dim)" : "var(--accent)"}
          stroke={isLeaf ? "var(--border)" : "color-mix(in srgb, var(--accent) 50%, transparent)"}
          strokeWidth={isLeaf ? 1 : 2.5}
        />
      </g>
    );
  };
}

export function TreeViz({ tree, featureNames, maxDepth = 99, onNodeClick }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 600, height: 400 });
  const [hover, setHover] = useState<HoverState | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const update = () => {
      const { width, height } = el.getBoundingClientRect();
      if (width > 0 && height > 0) setDimensions({ width, height });
    };
    update();
    const observer = new ResizeObserver(update);
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const allNodes = useMemo(() => flattenNodes(tree.root), [tree]);

  const d3Data = useMemo(
    () => toD3Node(tree.root, featureNames, 0, maxDepth),
    [tree, featureNames, maxDepth],
  );

  const handleNodeClick = (nodeDatum: RawNodeDatum) => {
    const nodeId = Number(nodeDatum.attributes?.id ?? -1);
    const found = allNodes.find((n) => n.id === nodeId);
    if (found) onNodeClick(found);
  };

  const translate = useMemo(
    () => ({ x: dimensions.width / 2, y: 48 }),
    [dimensions.width],
  );

  // Stable custom node factory — recreated only when containerRef or setHover identity changes
  const CustomNode = useCallback(
    makeCustomNode(containerRef, setHover),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  return (
    <div
      ref={containerRef}
      data-testid="tree-viz-container"
      className="tree-viz"
      style={{ height: "460px", overflow: "hidden", position: "relative" }}
      onMouseLeave={() => setHover(null)}
    >
      <Suspense
        fallback={
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "var(--text-dim)", fontSize: "12px", fontFamily: "var(--font-mono)" }}>
            Loading tree renderer…
          </div>
        }
      >
        {dimensions.width > 0 && (
          <Tree
            data={d3Data}
            orientation="vertical"
            dimensions={dimensions}
            translate={translate}
            nodeSize={{ x: 60, y: 80 }}
            separation={{ siblings: 1.2, nonSiblings: 1.6 }}
            zoom={0.65}
            scaleExtent={{ min: 0.1, max: 3 }}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            onNodeClick={(node: any) => handleNodeClick(node.data as RawNodeDatum)}
            renderCustomNodeElement={(props: CustomNodeElementProps) => (
              <CustomNode {...props} />
            )}
          />
        )}
      </Suspense>

      {hover && <NodeTooltip hover={hover} />}
    </div>
  );
}
