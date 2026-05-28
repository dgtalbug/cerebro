import js from "@eslint/js";
import globals from "globals";
import tseslint from "typescript-eslint";

export default tseslint.config(
  { ignores: ["dist", "src/lib/api/schema.d.ts"] },
  {
    files: ["src/**/*.{ts,tsx}"],
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
  },
  // Architectural boundary: views orchestrate primitives and fetch via query
  // hooks — they must never call `fetch` directly. Enforced mechanically so a
  // violation fails lint, not just review.
  {
    files: ["src/views/**/*.{ts,tsx}"],
    rules: {
      "no-restricted-globals": [
        "error",
        {
          name: "fetch",
          message:
            "Views must not call fetch directly — use a TanStack Query hook in lib/api/queries.",
        },
      ],
    },
  },
);
