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
