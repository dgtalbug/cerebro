import { Suspense, lazy, useMemo } from "react";
import type { RawNodeDatum, CustomNodeElementProps } from "react-d3-tree";
import type { ComponentType } from "react";

// react-d3-tree 3.x ships a class component whose getDerivedStateFromProps typing
// is narrower than React 18's generic GetDerivedStateFromProps<any,any>, which
// makes lazy() reject it. Cast via unknown to satisfy the module shape constraint.
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
  if (node.leaf_value !== null && node.left === null) {
    return {
      name: `leaf`,
      attributes: {
        value: node.leaf_value.toFixed(4),
        id: String(node.id),
      },
    };
  }
  const featName =
    node.split_feature !== null ? (featureNames[node.split_feature] ?? `f${node.split_feature}`) : "?";
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

function CustomNode({ nodeDatum }: CustomNodeElementProps) {
  const isLeaf = nodeDatum.name === "leaf";
  return (
    <g>
      <circle
        r={isLeaf ? 6 : 10}
        fill={isLeaf ? "var(--text-dim, #666)" : "var(--accent, #d4a574)"}
        stroke="var(--border, #333)"
        strokeWidth={1.5}
      />
      <text
        dy={isLeaf ? 20 : -16}
        textAnchor="middle"
        style={{ fontSize: "9px", fontFamily: "var(--font-mono, monospace)", fill: "var(--text, #ccc)" }}
      >
        {nodeDatum.name}
      </text>
    </g>
  );
}

export function TreeViz({ tree, featureNames, maxDepth = 99, onNodeClick }: Props) {
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

  return (
    <div
      data-testid="tree-viz-container"
      style={{ width: "100%", height: "400px", background: "var(--bg-elev)", borderRadius: "var(--radius)" }}
    >
      <Suspense
        fallback={
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100%", color: "var(--text-dim)", fontSize: "12px", fontFamily: "var(--font-mono)" }}>
            Loading tree renderer…
          </div>
        }
      >
        <Tree
          data={d3Data}
          orientation="vertical"
          translate={{ x: 300, y: 60 }}
          nodeSize={{ x: 160, y: 60 }}
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          onNodeClick={(node: any) => handleNodeClick(node.data as RawNodeDatum)}
          renderCustomNodeElement={(props: CustomNodeElementProps) => (
            <CustomNode {...props} />
          )}
        />
      </Suspense>
    </div>
  );
}
