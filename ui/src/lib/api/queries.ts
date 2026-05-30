import createClient from "openapi-fetch";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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
  provenance?: "measured" | "synthetic";
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
  provenance?: "measured" | "synthetic";
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

// ---- Model Registry -------------------------------------------------------

export interface SectionStatus {
  trees: boolean;
  importance: boolean;
  shap: boolean;
  evaluation: boolean;
  data_profile: boolean;
}

export interface ModelSummary {
  id: string;
  name: string;
  description: string | null;
  latest_version: number;
  latest_version_date: string;
  framework: string;
  objective: string;
  section_status: SectionStatus;
  created_at: string;
}

export interface VersionSummary {
  version: number;
  artifact_id: string;
  section_status: SectionStatus;
  notes: string | null;
  created_at: string;
}

export interface ModelDetail {
  id: string;
  name: string;
  description: string | null;
  versions: VersionSummary[];
  created_at: string;
}

export interface ModelFilters {
  framework?: string;
  objective?: string;
}

export function useModels(filters?: ModelFilters) {
  const params = new URLSearchParams();
  if (filters?.framework) params.set("framework", filters.framework);
  if (filters?.objective) params.set("objective", filters.objective);
  const qs = params.toString();

  return useQuery<ModelSummary[]>({
    queryKey: ["models", filters] as const,
    queryFn: async ({ signal }) => {
      const url = `${BASE_URL}/models${qs ? `?${qs}` : ""}`;
      const resp = await fetch(url, { signal });
      if (!resp.ok) throw new Error(`${resp.status}`);
      return resp.json() as Promise<ModelSummary[]>;
    },
    staleTime: 30_000,
    retry: false,
  });
}

export function useModel(id: string) {
  return useQuery<ModelDetail>({
    queryKey: ["model", id] as const,
    queryFn: async ({ signal }) => {
      const url = `${BASE_URL}/models/${encodeURIComponent(id)}`;
      const resp = await fetch(url, { signal });
      if (!resp.ok) throw new Error(`${resp.status}`);
      return resp.json() as Promise<ModelDetail>;
    },
    staleTime: 30_000,
    retry: false,
    enabled: !!id,
  });
}

export function useModelVersions(modelId: string) {
  return useQuery<VersionSummary[]>({
    queryKey: ["model", modelId, "versions"] as const,
    queryFn: async ({ signal }) => {
      const url = `${BASE_URL}/models/${encodeURIComponent(modelId)}/versions`;
      const resp = await fetch(url, { signal });
      if (!resp.ok) throw new Error(`${resp.status}`);
      return resp.json() as Promise<VersionSummary[]>;
    },
    staleTime: 30_000,
    retry: false,
    enabled: !!modelId,
  });
}

export interface EnrichParams {
  artifactId: string;
  modelFile?: File;
  samples?: File;
  labels?: File;
  trainingTable?: File;
}

export interface EnrichResponse {
  artifact_id: string;
  sections_added: string[];
  enriched_at: string;
}

export function useEnrichArtifact() {
  const queryClient = useQueryClient();
  return useMutation<EnrichResponse, Error, EnrichParams>({
    mutationFn: async (params) => {
      const form = new FormData();
      if (params.modelFile) form.append("model_file", params.modelFile);
      if (params.samples) form.append("samples", params.samples);
      if (params.labels) form.append("labels", params.labels);
      if (params.trainingTable) form.append("training_table", params.trainingTable);

      const resp = await fetch(
        `${BASE_URL}/artifacts/${encodeURIComponent(params.artifactId)}/enrich`,
        { method: "PATCH", body: form }
      );
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}));
        throw new Error(body.detail ?? `Enrich failed (${resp.status})`);
      }
      return resp.json() as Promise<EnrichResponse>;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["models"] });
      queryClient.invalidateQueries({ queryKey: ["artifact", variables.artifactId] });
    },
  });
}

export interface IngestResponse {
  model_id: string;
  model_name: string;
  version: number;
  artifact_id: string;
  sections: SectionStatus;
}

export interface IngestParams {
  model: File;
  modelName: string;
  notes?: string;
  samples?: File;
  labels?: File;
  evalSamples?: File;
  evalLabels?: File;
  trainingTable?: File;
}

export function useIngest() {
  const queryClient = useQueryClient();
  return useMutation<IngestResponse, Error, IngestParams>({
    mutationFn: async (params) => {
      const form = new FormData();
      form.append("model", params.model);
      form.append("model_name", params.modelName);
      if (params.notes) form.append("notes", params.notes);
      if (params.samples) form.append("samples", params.samples);
      if (params.labels) form.append("labels", params.labels);
      if (params.evalSamples) form.append("eval_samples", params.evalSamples);
      if (params.evalLabels) form.append("eval_labels", params.evalLabels);
      if (params.trainingTable) form.append("training_table", params.trainingTable);

      const resp = await fetch(`${BASE_URL}/artifacts/ingest`, {
        method: "POST",
        body: form,
      });
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({}));
        throw new Error(body.detail ?? `Extraction failed (${resp.status})`);
      }
      return resp.json() as Promise<IngestResponse>;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["models"] });
      queryClient.invalidateQueries({ queryKey: ["artifact", data.artifact_id] });
    },
  });
}

// ---- Agent ---------------------------------------------------------------

export interface AgentQueryRequest {
  artifact_id: string;
  question: string;
}

export interface AgentQueryResponse {
  answer: string;
  citations: string[];
}

export function useAgentQuery() {
  return useMutation<AgentQueryResponse, Error, AgentQueryRequest>({
    mutationFn: async (params) => {
      const resp = await fetch(`${BASE_URL}/agent/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(params),
      });
      if (resp.status === 503) {
        const body = await resp.json().catch(() => ({})) as { detail?: string };
        throw Object.assign(
          new Error(body.detail ?? "Agent not configured"),
          { status: 503 }
        );
      }
      if (!resp.ok) {
        const body = await resp.json().catch(() => ({})) as { detail?: string };
        throw new Error(body.detail ?? `Agent query failed (${resp.status})`);
      }
      return resp.json() as Promise<AgentQueryResponse>;
    },
  });
}

// ---- Diagnostics ---------------------------------------------------------

export interface Recommendation {
  kind: string;
  feature: string;
  reason: string;
  impact_estimate: string;
  details?: Record<string, string | number> | null;
}

export interface RedundancyWarning {
  weak_feature: string;
  dominant_feature: string;
  correlation: number;
  gain_ratio: number;
  confidence: number;
}

export interface LeakageWarning {
  feature: string;
  gain_rank: number;
  permutation_rank: number;
  delta: number;
}

export interface InteractionScore {
  feature_a: string;
  feature_b: string;
  score: number;
}

export interface FeatureDiagnostics {
  redundancy_warnings: RedundancyWarning[];
  leakage_warnings: LeakageWarning[];
  interactions: InteractionScore[];
  unused_features: string[];
  recommendations: Recommendation[];
  notes: string[];
}

export function useDiagnostics(id: string) {
  return useQuery<FeatureDiagnostics>({
    queryKey: ["diagnostics", id] as const,
    queryFn: async ({ signal }) => {
      const url = `${BASE_URL}/artifacts/${encodeURIComponent(id)}/diagnostics`;
      const resp = await fetch(url, { signal });
      if (!resp.ok) throw new Error(`${resp.status}`);
      return resp.json() as Promise<FeatureDiagnostics>;
    },
    staleTime: 5 * 60 * 1000,
    retry: false,
  });
}

// ---- Diff ----------------------------------------------------------------

export interface ImportanceDelta {
  feature: string;
  gain_a: number;
  gain_b: number;
  gain_delta: number;
  split_a: number;
  split_b: number;
  split_delta: number;
}

export interface FeatureSchemaDiff {
  added: string[];
  removed: string[];
}

export interface MetricDelta {
  metric: string;
  value_a: number;
  value_b: number;
  delta: number;
}

export interface CerebroDiff {
  artifact_a_id: string | null;
  artifact_b_id: string | null;
  schema_version_a: string;
  schema_version_b: string;
  framework_a: string;
  framework_b: string;
  objective_a: string;
  objective_b: string;
  importance_deltas: ImportanceDelta[];
  feature_schema_diff: FeatureSchemaDiff;
  metric_deltas: MetricDelta[];
  tree_count_delta: number;
}

export function useDiff(artifactId: string, compareId: string) {
  return useQuery<CerebroDiff>({
    queryKey: ["diff", artifactId, compareId] as const,
    queryFn: async ({ signal }) => {
      const url = `${BASE_URL}/artifacts/${encodeURIComponent(artifactId)}/diff/${encodeURIComponent(compareId)}`;
      const resp = await fetch(url, { signal });
      if (!resp.ok) throw new Error(`${resp.status}`);
      return resp.json() as Promise<CerebroDiff>;
    },
    staleTime: Infinity,
    retry: false,
    enabled: !!artifactId && !!compareId,
  });
}

// ---- Tags ----------------------------------------------------------------

export function useTags(artifactId: string) {
  return useQuery<{ tags: string[] }>({
    queryKey: ["tags", artifactId] as const,
    queryFn: async ({ signal }) => {
      const url = `${BASE_URL}/artifacts/${encodeURIComponent(artifactId)}/tags`;
      const resp = await fetch(url, { signal });
      if (!resp.ok) throw new Error(`${resp.status}`);
      return resp.json() as Promise<{ tags: string[] }>;
    },
    staleTime: 30_000,
    retry: false,
    enabled: !!artifactId,
  });
}

export function useAddTag(artifactId: string) {
  const queryClient = useQueryClient();
  return useMutation<{ artifact_id: string; tag: string }, Error, string>({
    mutationFn: async (tag) => {
      const resp = await fetch(`${BASE_URL}/artifacts/${encodeURIComponent(artifactId)}/tags`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ tag }),
      });
      if (!resp.ok) throw new Error(`${resp.status}`);
      return resp.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags", artifactId] });
    },
  });
}

export function useRemoveTag(artifactId: string) {
  const queryClient = useQueryClient();
  return useMutation<void, Error, string>({
    mutationFn: async (tag) => {
      const resp = await fetch(
        `${BASE_URL}/artifacts/${encodeURIComponent(artifactId)}/tags/${encodeURIComponent(tag)}`,
        { method: "DELETE" }
      );
      if (!resp.ok && resp.status !== 404) throw new Error(`${resp.status}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags", artifactId] });
    },
  });
}

// ---- Artifact list --------------------------------------------------------

export interface ArtifactRow {
  id: string;
  name: string;
  framework: string;
  objective: string;
  num_trees: number;
  num_features: number;
  schema_version: string;
  extracted_at: string;
}

export function useArtifactList(tag?: string) {
  const qs = tag ? `?tag=${encodeURIComponent(tag)}` : "";
  return useQuery<{ items: ArtifactRow[] }>({
    queryKey: ["artifact-list", tag] as const,
    queryFn: async ({ signal }) => {
      const resp = await fetch(`${BASE_URL}/artifacts${qs}`, { signal });
      if (!resp.ok) throw new Error(`${resp.status}`);
      return resp.json() as Promise<{ items: ArtifactRow[] }>;
    },
    staleTime: 30_000,
    retry: false,
  });
}
