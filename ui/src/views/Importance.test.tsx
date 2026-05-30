// @vitest-environment jsdom

import type { ReactNode } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { cleanup, render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { Importance } from "./Importance";
import { useImportance } from "../lib/api/queries";
import type { ImportanceResponse } from "../lib/api/queries";

vi.mock("../lib/api/queries", () => {
  const mockUseImportance = vi.fn();
  const mockUseDiagnostics = vi.fn().mockReturnValue({ data: null, isLoading: false });
  return { useImportance: mockUseImportance, useDiagnostics: mockUseDiagnostics };
});

function Wrapper({ children }: { children: ReactNode }) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return (
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/artifacts/test-id/importance"]}>
        {children}
      </MemoryRouter>
    </QueryClientProvider>
  );
}

const gainData: ImportanceResponse = {
  artifact_id: "test-id",
  type: "gain",
  features: [
    { name: "credit_score", value: 2847.3, rank_gain: 1 },
    { name: "debt_to_income", value: 2218.6, rank_gain: 2 },
    { name: "annual_income", value: 1824.0, rank_gain: 3 },
  ],
};

const permNoData: ImportanceResponse = {
  artifact_id: "test-id",
  type: "permutation",
  features: [],
  detail: "permutation importance was not computed — no evaluation samples were provided at extraction time",
};

const permWithData: ImportanceResponse = {
  artifact_id: "test-id",
  type: "permutation",
  features: [
    { name: "credit_score", value: 0.12, std: 0.01, rank_gain: 1 },
    { name: "debt_to_income", value: 0.09, std: 0.02, rank_gain: 2 },
    { name: "annual_income", value: 0.07, std: 0.01, rank_gain: 3 },
  ],
  divergence_warnings: [
    { feature: "annual_income", gain_rank: 3, permutation_rank: 1, delta: 2 },
  ],
};

function mockImportance(type: string, data: ImportanceResponse) {
  vi.mocked(useImportance).mockImplementation((_, t) =>
    t === type
      ? ({ data, isLoading: false, isError: false, error: null } as ReturnType<typeof useImportance>)
      : ({ data: gainData, isLoading: false, isError: false, error: null } as ReturnType<typeof useImportance>),
  );
}

beforeEach(() => vi.clearAllMocks());
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});

describe("Importance view", () => {
  it("renders the view header", () => {
    mockImportance("gain", gainData);
    render(<Importance />, { wrapper: Wrapper });
    expect(screen.getByText("importance")).toBeTruthy();
  });

  it("renders gain bars by default", () => {
    mockImportance("gain", gainData);
    render(<Importance />, { wrapper: Wrapper });
    expect(screen.getAllByText("credit_score").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("2847.30").length).toBeGreaterThanOrEqual(1);
  });

  it("has three tab buttons", () => {
    mockImportance("gain", gainData);
    render(<Importance />, { wrapper: Wrapper });
    expect(screen.getByTestId("tab-gain")).toBeTruthy();
    expect(screen.getByTestId("tab-split")).toBeTruthy();
    expect(screen.getByTestId("tab-permutation")).toBeTruthy();
  });

  it("switching to split tab re-queries with split type", () => {
    vi.mocked(useImportance).mockReturnValue({
      data: gainData,
      isLoading: false,
      isError: false,
      error: null,
    } as ReturnType<typeof useImportance>);

    render(<Importance />, { wrapper: Wrapper });
    fireEvent.click(screen.getByTestId("tab-split"));

    expect(vi.mocked(useImportance)).toHaveBeenCalledWith(expect.any(String), "split");
  });

  it("shows not-computed message when permutation has detail", () => {
    vi.mocked(useImportance).mockImplementation((_, t) =>
      t === "permutation"
        ? ({ data: permNoData, isLoading: false, isError: false, error: null } as ReturnType<typeof useImportance>)
        : ({ data: gainData, isLoading: false, isError: false, error: null } as ReturnType<typeof useImportance>),
    );

    render(<Importance />, { wrapper: Wrapper });
    fireEvent.click(screen.getByTestId("tab-permutation"));

    expect(screen.getAllByText(/not computed/).length).toBeGreaterThanOrEqual(1);
  });

  it("renders divergence callout when warnings present", () => {
    vi.mocked(useImportance).mockImplementation((_, t) =>
      t === "permutation"
        ? ({ data: permWithData, isLoading: false, isError: false, error: null } as ReturnType<typeof useImportance>)
        : ({ data: gainData, isLoading: false, isError: false, error: null } as ReturnType<typeof useImportance>),
    );

    render(<Importance />, { wrapper: Wrapper });
    fireEvent.click(screen.getByTestId("tab-permutation"));

    expect(screen.getAllByTestId("divergence-callout").length).toBeGreaterThanOrEqual(1);
  });

  it("does not render divergence callout when no warnings", () => {
    mockImportance("gain", gainData);
    render(<Importance />, { wrapper: Wrapper });
    expect(screen.queryByTestId("divergence-callout")).toBeNull();
  });
});
