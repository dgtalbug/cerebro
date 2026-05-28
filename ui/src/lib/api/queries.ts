import createClient from "openapi-fetch";
import { useQuery } from "@tanstack/react-query";
import type { paths } from "./schema";

const BASE_URL: string = import.meta.env.VITE_API_URL ?? "/api";

export const client = createClient<paths>({ baseUrl: BASE_URL });

export function useArtifact(id: string) {
  return useQuery({
    queryKey: ["artifact", id] as const,
    queryFn: ({ signal }) =>
      client.GET("/artifacts/{artifact_id}", {
        params: { path: { artifact_id: id } },
        signal,
      }),
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

export type ImportanceType = "gain" | "split" | "permutation";

export interface ImportanceFeature {
  name: string;
  value: number;
  std?: number;
  rank_gain?: number;
  rank_divergence?: number | null;
}

export interface DivergenceWarning {
  feature: string;
  gain_rank: number;
  permutation_rank: number;
  delta: number;
}

export interface ImportanceResponse {
  artifact_id: string;
  type: ImportanceType;
  features: ImportanceFeature[];
  detail?: string;
  divergence_warnings?: DivergenceWarning[];
}

export function useImportance(id: string, type: ImportanceType) {
  return useQuery<ImportanceResponse>({
    queryKey: ["importance", id, type] as const,
    queryFn: async ({ signal }) => {
      const url = `${BASE_URL}/artifacts/${encodeURIComponent(id)}/importance?type=${type}`;
      const resp = await fetch(url, { signal });
      if (!resp.ok) throw new Error(`${resp.status}`);
      return resp.json() as Promise<ImportanceResponse>;
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

// ---- Data Profile --------------------------------------------------------

export interface HistogramBin { lower: number; upper: number; count: number }
export interface CategoryCount { value: string; count: number }
export interface ColumnProfile {
  name: string; dtype: string; is_numeric: boolean; is_categorical: boolean;
  total_rows: number; null_count: number; missingness: number;
  histogram?: HistogramBin[] | null;
  top_categories?: CategoryCount[] | null;
  min?: number | null; max?: number | null; mean?: number | null; std?: number | null;
}
export interface CorrelationCell { feature_a: string; feature_b: string; pearson: number }
export interface DataProfileResponse {
  row_count: number; column_count: number;
  columns: ColumnProfile[]; correlations: CorrelationCell[];
  detail?: string;
}

export function useDataProfile(id: string) {
  return useQuery<DataProfileResponse>({
    queryKey: ["data-profile", id] as const,
    queryFn: async ({ signal }) => {
      const url = `${BASE_URL}/artifacts/${encodeURIComponent(id)}/data-profile`;
      const resp = await fetch(url, { signal });
      if (!resp.ok) throw new Error(`${resp.status}`);
      return resp.json() as Promise<DataProfileResponse>;
    },
    staleTime: Infinity,
    retry: false,
  });
}

// ---- Explanations --------------------------------------------------------

export interface ShapStep { feature: string; value: number }
export interface DecisionStep {
  node_id: number; feature_index: number; feature_name: string;
  threshold: number | null; decision_type: string;
  sample_value: number; went_left: boolean;
}
export interface DecisionPath { tree_index: number; steps: DecisionStep[]; leaf_value: number }
export interface PDPFeature {
  feature: string; feature_index: number;
  grid: number[]; values: number[]; is_categorical: boolean;
}
export interface ShapResult {
  expected_value: number | number[];
  shap_values: number[][] | number[][][];
  feature_names: string[];
  sample_count: number;
  background_sample_count: number;
}
export interface ExplanationsResponse {
  shap?: ShapResult | null;
  decision_paths?: DecisionPath[][] | null;
  partial_dependence?: PDPFeature[] | null;
  detail?: string;
}

export function useExplanations(id: string) {
  return useQuery<ExplanationsResponse>({
    queryKey: ["explanations", id] as const,
    queryFn: async ({ signal }) => {
      const url = `${BASE_URL}/artifacts/${encodeURIComponent(id)}/explanations`;
      const resp = await fetch(url, { signal });
      if (!resp.ok) throw new Error(`${resp.status}`);
      return resp.json() as Promise<ExplanationsResponse>;
    },
    staleTime: Infinity,
    retry: false,
  });
}

// ---- Evaluation ----------------------------------------------------------

export interface ROCPoint { fpr: number; tpr: number; threshold: number }
export interface ConfusionCell { predicted: number; actual: number; count: number }
export interface PerClassMetrics {
  class_index: number; precision: number; recall: number; f1: number; support: number;
}
export interface NDCGAtK { k: number; value: number }
export interface EvalHistogramBin { lower: number; upper: number; count: number }
export interface ScatterPoint { predicted: number; actual: number }
export interface IntervalPoint { predicted: number; lower: number; upper: number }

export interface BinaryEval {
  objective: "binary"; auc: number; roc_curve: ROCPoint[];
  confusion_matrix: ConfusionCell[]; threshold: number;
  precision: number; recall: number; f1: number;
}
export interface MulticlassEval {
  objective: "multiclass"; confusion_matrix: ConfusionCell[];
  per_class: PerClassMetrics[]; macro_f1: number; accuracy: number;
}
export interface RegressionEval {
  objective: "regression"; rmse: number; mae: number; r2: number;
  residuals_histogram: EvalHistogramBin[];
  scatter: ScatterPoint[]; interval_band: IntervalPoint[];
}
export interface RankingEval {
  objective: "lambdarank"; ndcg_at_k: NDCGAtK[];
  mean_average_precision: number; per_query_ndcg: number[];
}
export type AnyEval = BinaryEval | MulticlassEval | RegressionEval | RankingEval;
export interface EvaluationResponse { detail?: string }

export function useEvaluation(id: string) {
  return useQuery<AnyEval | EvaluationResponse>({
    queryKey: ["evaluation", id] as const,
    queryFn: async ({ signal }) => {
      const url = `${BASE_URL}/artifacts/${encodeURIComponent(id)}/evaluation`;
      const resp = await fetch(url, { signal });
      if (!resp.ok) throw new Error(`${resp.status}`);
      return resp.json() as Promise<AnyEval | EvaluationResponse>;
    },
    staleTime: Infinity,
    retry: false,
  });
}
