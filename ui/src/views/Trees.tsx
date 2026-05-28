import { useState, useMemo } from "react";
import { useParams } from "react-router-dom";
import { ViewHeader } from "../components/layout/ViewHeader";
import { TreeControls } from "../components/trees/TreeControls";
import { TreeViz } from "../components/trees/TreeViz";
import { NodeInspector } from "../components/trees/NodeInspector";
import { useArtifact } from "../lib/api/queries";

interface CanonicalNode {
  id: number;
  split_feature: number | null;
  threshold: number | null;
  decision_type: string | null;
  left: CanonicalNode | null;
  right: CanonicalNode | null;
  leaf_value: number | null;
}

interface SelectedNode {
  id: number;
  split_feature: number | null;
  threshold: number | null;
  decision_type: string | null;
  leaf_value: number | null;
}

function countNodes(node: CanonicalNode): { nodes: number; leaves: number } {
  if (node.left === null && node.right === null) return { nodes: 1, leaves: 1 };
  const left = node.left ? countNodes(node.left) : { nodes: 0, leaves: 0 };
  const right = node.right ? countNodes(node.right) : { nodes: 0, leaves: 0 };
  return { nodes: 1 + left.nodes + right.nodes, leaves: left.leaves + right.leaves };
}

export function Trees() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading, isError, error } = useArtifact(id ?? "placeholder");

  const [selectedTreeIndex, setSelectedTreeIndex] = useState(0);
  const [maxDepth, setMaxDepth] = useState<number | null>(null);
  const [selectedNode, setSelectedNode] = useState<SelectedNode | null>(null);

  const artifact = data?.data;
  const trees = (artifact?.trees ?? []) as unknown as Array<{
    index: number;
    class_index: number | null;
    num_leaves: number;
    root: CanonicalNode;
  }>;
  const featureNames = artifact?.model.feature_schema.names ?? [];
  const selectedTree = trees[selectedTreeIndex] ?? trees[0];

  const { nodes: nodeCount, leaves: leafCount } = useMemo(
    () => (selectedTree ? countNodes(selectedTree.root) : { nodes: 0, leaves: 0 }),
    [selectedTree],
  );

  if (isLoading) {
    return (
      <section className="view">
        <ViewHeader title="Tree" titleEmphasis="topology" subtitle="Loading artifact…" />
        <div style={{ color: "var(--text-dim)", fontFamily: "var(--font-mono)", fontSize: "12px", padding: "24px 0" }}>
          Fetching canonical artifact from API…
        </div>
      </section>
    );
  }

  if (isError || !artifact) {
    return (
      <section className="view">
        <ViewHeader
          title="Tree"
          titleEmphasis="topology"
          subtitle={error?.message?.includes?.("404") ? "Artifact not found." : "Failed to load artifact."}
        />
        <div style={{ color: "var(--red, #e74c3c)", fontSize: "12px" }}>
          Could not load artifact.
        </div>
      </section>
    );
  }

  if (trees.length === 0) {
    return (
      <section className="view">
        <ViewHeader title="Tree" titleEmphasis="topology" subtitle="No trees in artifact." />
        <div style={{ color: "var(--text-dim)", fontSize: "12px" }}>
          This artifact contains no trees.
        </div>
      </section>
    );
  }

  return (
    <section className="view">
      <ViewHeader
        title="Tree"
        titleEmphasis="topology"
        subtitle="Every split, every threshold, every leaf — extracted from the booster. Click any node to inspect."
      />

      <TreeControls
        trees={trees}
        selectedIndex={selectedTreeIndex}
        depth={maxDepth}
        nodeCount={nodeCount}
        leafCount={leafCount}
        onTreeChange={(idx) => {
          setSelectedTreeIndex(idx);
          setSelectedNode(null);
        }}
        onDepthChange={setMaxDepth}
      />

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 280px",
          gap: "24px",
          alignItems: "start",
        }}
      >
        {selectedTree && (
          <TreeViz
            tree={selectedTree}
            featureNames={featureNames}
            maxDepth={maxDepth ?? 99}
            onNodeClick={(node) => setSelectedNode(node)}
          />
        )}

        <div
          style={{
            background: "var(--bg-elev)",
            border: "1px solid var(--border)",
            borderRadius: "var(--radius)",
            padding: "16px",
            minHeight: "120px",
          }}
        >
          <div style={{ fontSize: "11px", fontFamily: "var(--font-mono)", color: "var(--text-dim)", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "12px" }}>
            Node inspector
          </div>
          <NodeInspector node={selectedNode} featureNames={featureNames} />
        </div>
      </div>
    </section>
  );
}
