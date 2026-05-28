import createClient from "openapi-fetch";
import { useQuery } from "@tanstack/react-query";
import type { paths } from "./schema";

const BASE_URL: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

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
