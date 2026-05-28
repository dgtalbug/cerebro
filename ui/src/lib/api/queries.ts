// Server access lives here, behind hooks. Views import from this module and
// never call `fetch` themselves (enforced by eslint.config.js). The TanStack
// Query hooks (useArtifact, useTree, ...) are added against the generated API
// client (see `pnpm api:types`).

export const API_URL: string = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
