// @vitest-environment jsdom

import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Trees } from "./Trees";
import { useArtifact } from "../lib/api/queries";

// Mock react-d3-tree to avoid SVG/ResizeObserver issues in jsdom
vi.mock("react-d3-tree", () => ({
  default: ({ data, onNodeClick }: { data: { name: string }; onNodeClick: (n: { data: { name: string; attributes?: Record<string, string> } }) => void }) => (
    <div data-testid="mock-tree-viz" data-tree-name={data.name}>
      <button
        data-testid="mock-node-click"
        onClick={() =>
          onNodeClick({
            data: { name: "credit_score <= 680.500", attributes: { id: "0", feat: "0" } },
          })
        }
      >
        Click node
      </button>
    </div>
  ),
}));

vi.mock("../lib/api/queries", () => ({
  useArtifact: vi.fn(),
  client: {},
}));

function Wrapper({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/artifacts/test-id/trees"]}>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  );
}

function makeLeaf(id: number, value: number) {
  return { id, split_feature: null, threshold: null, decision_type: null, left: null, right: null, leaf_value: value };
}

function makeSplit(id: number, feat: number, thresh: number, left: object, right: object) {
  return { id, split_feature: feat, threshold: thresh, decision_type: "<=", left, right, leaf_value: null };
}

const tree0 = {
  index: 0,
  class_index: null,
  num_leaves: 2,
  root: makeSplit(0, 0, 680.5, makeLeaf(1, -0.1), makeLeaf(2, 0.1)),
};
const tree1 = {
  index: 1,
  class_index: null,
  num_leaves: 2,
  root: makeSplit(0, 1, 0.42, makeLeaf(1, -0.05), makeLeaf(2, 0.05)),
};
const tree2 = {
  index: 2,
  class_index: null,
  num_leaves: 2,
  root: makeSplit(0, 2, 50000.0, makeLeaf(1, -0.08), makeLeaf(2, 0.08)),
};

const fixture = {
  schema_version: "1.0.0" as const,
  source: { framework: "lightgbm" as const, framework_version: "4.6.0", extracted_at: "2026-05-28T12:00:00Z", extractor_version: "0.1.0" },
  model: {
    objective: "binary" as const,
    num_class: 1,
    num_iteration: 3,
    params: {},
    feature_schema: { names: ["credit_score", "debt_to_income", "annual_income"], categorical_indices: [], monotone_constraints: [0, 0, 0] },
  },
  trees: [tree0, tree1, tree2],
  importance: { gain: { credit_score: 1.0, debt_to_income: 0.5, annual_income: 0.3 }, split: { credit_score: 5, debt_to_income: 3, annual_income: 2 }, permutation: null, divergence_warnings: null },
  rank_metadata: null,
  explanations: null,
  evaluation: null,
};

function mockSuccess() {
  vi.mocked(useArtifact).mockReturnValue({
    data: { data: fixture },
    isLoading: false,
    isError: false,
    error: null,
  } as unknown as ReturnType<typeof useArtifact>);
}

beforeEach(() => vi.clearAllMocks());
afterEach(() => { cleanup(); vi.clearAllMocks(); });

describe("Trees view", () => {
  it("renders the view header", () => {
    mockSuccess();
    render(<Trees />, { wrapper: Wrapper });
    expect(screen.getByText("topology")).toBeTruthy();
  });

  it("renders three options in the tree selector", () => {
    mockSuccess();
    render(<Trees />, { wrapper: Wrapper });
    const selector = screen.getByTestId("tree-selector") as HTMLSelectElement;
    expect(selector.options.length).toBe(3);
  });

  it("selecting a different tree changes the selected index", () => {
    mockSuccess();
    render(<Trees />, { wrapper: Wrapper });
    const selector = screen.getByTestId("tree-selector") as HTMLSelectElement;
    fireEvent.change(selector, { target: { value: "2" } });
    expect(selector.value).toBe("2");
  });

  it("shows the tree visualisation container", () => {
    mockSuccess();
    render(<Trees />, { wrapper: Wrapper });
    expect(screen.getByTestId("mock-tree-viz")).toBeTruthy();
  });

  it("shows empty inspector before a node is clicked", () => {
    mockSuccess();
    render(<Trees />, { wrapper: Wrapper });
    expect(screen.getByTestId("node-inspector-empty")).toBeTruthy();
  });

  it("node click populates the inspector", () => {
    mockSuccess();
    render(<Trees />, { wrapper: Wrapper });
    fireEvent.click(screen.getByTestId("mock-node-click"));
    expect(screen.getByTestId("node-inspector")).toBeTruthy();
  });

  it("renders depth filter buttons", () => {
    mockSuccess();
    render(<Trees />, { wrapper: Wrapper });
    expect(screen.getByTestId("depth-all")).toBeTruthy();
    expect(screen.getByTestId("depth-3")).toBeTruthy();
    expect(screen.getByTestId("depth-4")).toBeTruthy();
    expect(screen.getByTestId("depth-5")).toBeTruthy();
  });

  it("shows loading state", () => {
    vi.mocked(useArtifact).mockReturnValue({ data: undefined, isLoading: true, isError: false, error: null } as unknown as ReturnType<typeof useArtifact>);
    render(<Trees />, { wrapper: Wrapper });
    expect(screen.getByText("Loading artifact…")).toBeTruthy();
  });
});
