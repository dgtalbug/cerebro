# docs/

This directory is **reserved for Cerebro's published documentation site and
guide** — the user-facing docs that ship in MVP 1 (roadmap E1.050: README,
schema spec, CLI guide, "build your own viz" guide). It is tracked in git and
will become the source of the documentation site.

It is intentionally empty for now; documentation content lands as the product
does.

## Where the design narrative lives

The locked design narrative and working discussion (the original
`cerebro-open-spec.md`, `BACKEND.md`, `FRONTEND.md`, `DATABASE.md`, `DOCKER.md`,
`ROADMAP.md`, the mockup, etc.) live in the top-level **`.docs/`** directory,
which is **git-ignored** (personal/working "meta" material).

> Note: the OpenSpec specs under `openspec/specs/` cross-reference
> `.docs/cerebro-open-spec.md`. Because `.docs/` is not version-controlled,
> those references resolve only in a local working copy that has the narrative
> present.
