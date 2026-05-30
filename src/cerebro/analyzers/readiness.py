"""Dashboard readiness assessment.

Maps a model (and optionally an already-extracted artifact) to per-tab
readiness: which dashboard tabs are satisfiable, what input each unmet tab
needs, and whether that input requires ground-truth labels. The feature
contract — the exact ordered feature names the model expects — is surfaced so a
supplied sample matrix can be aligned to it.

This is a read-only diagnostic; it never extracts or writes anything.
"""

from __future__ import annotations

from dataclasses import dataclass

from cerebro.schema import CerebroArtifact


@dataclass(frozen=True)
class TabReadiness:
    """Readiness of a single dashboard tab."""

    name: str
    satisfiable: bool
    requires_labels: bool
    missing_inputs: tuple[str, ...]


@dataclass(frozen=True)
class ReadinessReport:
    """Per-tab readiness plus the model's feature contract."""

    feature_names: tuple[str, ...]
    tabs: tuple[TabReadiness, ...]

    @property
    def feature_count(self) -> int:
        return len(self.feature_names)

    def is_ready(self) -> bool:
        """True when every tab is satisfiable (nothing is missing inputs)."""
        return all(tab.satisfiable for tab in self.tabs)

    def to_dict(self) -> dict[str, object]:
        """Machine-readable form for `--json` output."""
        return {
            "feature_count": self.feature_count,
            "feature_names": list(self.feature_names),
            "is_ready": self.is_ready(),
            "tabs": [
                {
                    "name": tab.name,
                    "satisfiable": tab.satisfiable,
                    "requires_labels": tab.requires_labels,
                    "missing_inputs": list(tab.missing_inputs),
                }
                for tab in self.tabs
            ],
        }


def _has_permutation(artifact: CerebroArtifact | None) -> bool:
    if artifact is None:
        return False
    return bool(artifact.importance.permutation)


def assess_readiness(
    feature_names: list[str],
    artifact: CerebroArtifact | None = None,
) -> ReadinessReport:
    """Assess dashboard readiness from feature names and an optional artifact.

    Model-only tabs (Overview, Trees, gain/split importance) are always
    satisfiable. Data-dependent tabs are satisfiable only when the supplied
    artifact already has the corresponding section populated; otherwise they
    report the inputs still required.
    """
    explanations_ok = artifact is not None and artifact.explanations is not None
    evaluation_ok = artifact is not None and artifact.evaluation is not None
    profile_ok = artifact is not None and artifact.data_profile is not None
    permutation_ok = _has_permutation(artifact)

    tabs = (
        TabReadiness("Overview", True, False, ()),
        TabReadiness("Trees", True, False, ()),
        TabReadiness("Importance (gain/split)", True, False, ()),
        TabReadiness(
            "Importance (permutation)",
            permutation_ok,
            True,
            () if permutation_ok else ("samples", "labels"),
        ),
        TabReadiness(
            "Explanations",
            explanations_ok,
            False,
            () if explanations_ok else ("samples",),
        ),
        TabReadiness(
            "Evaluation",
            evaluation_ok,
            True,
            () if evaluation_ok else ("eval_samples", "eval_labels"),
        ),
        TabReadiness(
            "Data Profile",
            profile_ok,
            False,
            () if profile_ok else ("training_table",),
        ),
    )

    return ReadinessReport(feature_names=tuple(feature_names), tabs=tabs)
