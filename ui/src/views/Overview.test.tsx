// @vitest-environment jsdom

import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Overview } from "../views/Overview";
import { useArtifact } from "../lib/api/queries";

vi.mock("../lib/api/queries", () => {
  const mockUseArtifact = vi.fn();
  return {
    useArtifact: mockUseArtifact,
    client: {},
  };
});

function Wrapper({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/artifacts/fixture-1/overview"]}>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const fixture = {
  schema_version: "1.0.0" as const,
  source: {
    framework: "lightgbm" as const,
    framework_version: "4.6.0",
    extracted_at: "2026-05-28T11:42:03Z",
    extractor_version: "0.1.0",
  },
  model: {
    objective: "binary" as const,
    num_class: 1 as const,
    num_iteration: 50,
    params: {
      learning_rate: 0.05,
      num_leaves: 31,
      max_depth: 6,
      min_data_in_leaf: 20,
    },
    feature_schema: {
      names: ["credit_score", "debt_to_income", "annual_income", "loan_purpose"],
      categorical_indices: [3],
      monotone_constraints: [1, 0, -1, 0],
    },
  },
  trees: [],
  importance: {
    gain: { credit_score: 0.42 },
    split: { credit_score: 120 },
    permutation: null,
  },
  explanations: null,
  evaluation: null,
};

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

function mockSuccess(data: typeof fixture) {
  vi.mocked(useArtifact).mockReturnValue({
    data: { data },
    isLoading: false,
    isError: false,
    error: null,
  } as unknown as ReturnType<typeof useArtifact>);
}

function mockLoading() {
  vi.mocked(useArtifact).mockReturnValue({
    data: undefined,
    isLoading: true,
    isError: false,
    error: null,
  } as unknown as ReturnType<typeof useArtifact>);
}

function mockError(errorMessage: string) {
  vi.mocked(useArtifact).mockReturnValue({
    data: undefined,
    isLoading: false,
    isError: true,
    error: new Error(errorMessage),
  } as unknown as ReturnType<typeof useArtifact>);
}

describe("Overview", () => {
  it("renders the four stat tiles with correct values", () => {
    mockSuccess(fixture);
    render(<Overview />, { wrapper: Wrapper });

    expect(screen.getByText("binary")).toBeTruthy();
    expect(screen.getAllByText("50").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("4")).toBeTruthy();
    expect(screen.getByText("no samples at extraction time")).toBeTruthy();
  });

  it("renders the training params panel", () => {
    mockSuccess(fixture);
    render(<Overview />, { wrapper: Wrapper });

    expect(screen.getAllByText("Training parameters").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("learning_rate").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("0.05").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("num_leaves").length).toBeGreaterThanOrEqual(1);
  });

  it("renders feature schema with type colours and constraint labels", () => {
    mockSuccess(fixture);
    render(<Overview />, { wrapper: Wrapper });

    expect(screen.getAllByText("credit_score").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("loan_purpose").length).toBeGreaterThanOrEqual(1);

    const numericEls = screen.getAllByText("numeric");
    expect(numericEls.length).toBeGreaterThanOrEqual(1);
    expect(numericEls[0]!.style.color).toBe("var(--blue)");

    const catEls = screen.getAllByText("categorical");
    expect(catEls.length).toBeGreaterThanOrEqual(1);
    expect(catEls[0]!.style.color).toBe("var(--purple)");

    const monoPlus = screen.getAllByText("mono+");
    expect(monoPlus.length).toBeGreaterThanOrEqual(1);
    expect(monoPlus[0]!.style.color).toBe("var(--accent)");

    const monoMinus = screen.getAllByText("mono-");
    expect(monoMinus.length).toBeGreaterThanOrEqual(1);
    expect(monoMinus[0]!.style.color).toBe("var(--accent)");
  });

  it("shows loading state when fetching", () => {
    mockLoading();
    render(<Overview />, { wrapper: Wrapper });

    expect(screen.getByText("Loading artifact…")).toBeTruthy();
  });

  it("shows error state when fetch fails", () => {
    mockError("500: Internal Server Error");
    render(<Overview />, { wrapper: Wrapper });

    expect(screen.getByText("Failed to load artifact.")).toBeTruthy();
  });

  it("shows 404 message when artifact not found", () => {
    mockError("404");
    render(<Overview />, { wrapper: Wrapper });

    expect(screen.getByText("Artifact not found.")).toBeTruthy();
    expect(
      screen.getByText(
        "The requested artifact could not be found. Check the artifact ID and try again.",
      ),
    ).toBeTruthy();
  });
});
