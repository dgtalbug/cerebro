"""Feature diagnostics analyzer.

All analysis is derived from the canonical CerebroArtifact — no ML framework
required at runtime. Results are returned as a FeatureDiagnostics object
suitable for inclusion in a v1.1.0 artifact.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from cerebro.schema.v1_1.feature_diagnostics import (
    FeatureDiagnostics,
    InteractionScore,
    LeakageWarning,
    Recommendation,
    RedundancyWarning,
)

if TYPE_CHECKING:
    from cerebro.schema.v1_1.artifact import CerebroArtifact
    from cerebro.schema.v1_1.tree import TreeNode

_CORRELATION_THRESHOLD = 0.85
_GAIN_RATIO_THRESHOLD = 0.15
_LEAKAGE_RANK_DELTA = 0.25
_TOP_INTERACTIONS = 50
_STRONG_INTERACTION_THRESHOLD = 0.5


def compute_diagnostics(artifact: CerebroArtifact) -> FeatureDiagnostics:
    """Derive feature diagnostics from a canonical artifact."""
    feature_names = artifact.model.feature_schema.names

    redundancy = _detect_redundancy(artifact, feature_names)
    leakage = _detect_leakage(artifact, feature_names)
    interactions = _compute_interactions(artifact, feature_names)
    unused = _detect_unused(artifact, feature_names)
    recommendations = _build_recommendations(
        redundancy, leakage, interactions, unused, artifact.importance.gain
    )
    notes: list[str] = []
    if artifact.data_profile is None:
        notes.append("data_profile absent — redundancy detection skipped")
    if artifact.importance.permutation is None:
        notes.append("permutation importance absent — leakage detection skipped")

    return FeatureDiagnostics(
        redundancy_warnings=redundancy,
        leakage_warnings=leakage,
        interactions=interactions,
        unused_features=unused,
        recommendations=recommendations,
        notes=notes,
    )


def _detect_redundancy(
    artifact: CerebroArtifact, feature_names: list[str]
) -> list[RedundancyWarning]:
    if artifact.data_profile is None:
        return []

    corr_map: dict[tuple[str, str], float] = {}
    for cell in artifact.data_profile.correlations:
        corr_map[(cell.feature_a, cell.feature_b)] = cell.pearson
        corr_map[(cell.feature_b, cell.feature_a)] = cell.pearson

    gain = artifact.importance.gain
    warnings: list[RedundancyWarning] = []
    checked: set[frozenset[str]] = set()

    for fa in feature_names:
        for fb in feature_names:
            if fa == fb:
                continue
            pair = frozenset([fa, fb])
            if pair in checked:
                continue
            checked.add(pair)
            r = abs(corr_map.get((fa, fb), corr_map.get((fb, fa), 0.0)))
            if r < _CORRELATION_THRESHOLD:
                continue
            gain_a = gain.get(fa, 0.0)
            gain_b = gain.get(fb, 0.0)
            if gain_a == 0.0 and gain_b == 0.0:
                continue
            if gain_a >= gain_b:
                dominant, weak = fa, fb
                ratio = gain_b / gain_a if gain_a > 0 else 0.0
            else:
                dominant, weak = fb, fa
                ratio = gain_a / gain_b if gain_b > 0 else 0.0
            if ratio > _GAIN_RATIO_THRESHOLD:
                continue
            confidence = min(1.0, r * (1.0 - ratio))
            warnings.append(
                RedundancyWarning(
                    weak_feature=weak,
                    dominant_feature=dominant,
                    correlation=round(r, 4),
                    gain_ratio=round(ratio, 4),
                    confidence=round(confidence, 4),
                )
            )
    return sorted(warnings, key=lambda w: w.confidence, reverse=True)


def _detect_leakage(
    artifact: CerebroArtifact, feature_names: list[str]
) -> list[LeakageWarning]:
    if artifact.importance.permutation is None:
        return []

    gain = artifact.importance.gain
    perm = artifact.importance.permutation

    # rank by gain descending
    gain_ranked = [
        f for f, _ in sorted(gain.items(), key=lambda x: x[1], reverse=True)
        if f in perm
    ]
    # rank by permutation mean descending
    perm_ranked = [
        f for f, _ in sorted(
            ((f, v.get("mean", 0.0)) for f, v in perm.items() if f in gain),
            key=lambda x: x[1],
            reverse=True,
        )
    ]

    n = len(gain_ranked)
    threshold = max(1, int(n * _LEAKAGE_RANK_DELTA))
    warnings: list[LeakageWarning] = []

    for gain_rank, feat in enumerate(gain_ranked):
        if gain_rank >= n // 2:
            continue
        if feat not in perm_ranked:
            continue
        perm_rank = perm_ranked.index(feat)
        delta = perm_rank - gain_rank
        if delta > threshold:
            warnings.append(
                LeakageWarning(
                    feature=feat,
                    gain_rank=gain_rank + 1,
                    permutation_rank=perm_rank + 1,
                    delta=delta,
                )
            )
    return sorted(warnings, key=lambda w: w.delta, reverse=True)


def _compute_interactions(
    artifact: CerebroArtifact, feature_names: list[str]
) -> list[InteractionScore]:
    """Co-occurrence frequency normalized by individual split counts."""
    co: dict[tuple[int, int], int] = {}
    splits: dict[int, int] = {}

    for tree in artifact.trees:
        _walk_paths_for_cooccurrence(tree.root, [], co, splits)

    if not splits:
        return []

    scores: list[InteractionScore] = []
    seen: set[frozenset[int]] = set()
    for (a, b), count in co.items():
        pair = frozenset([a, b])
        if pair in seen or a == b:
            continue
        seen.add(pair)
        denom = math.sqrt(splits.get(a, 1) * splits.get(b, 1))
        score = count / denom if denom > 0 else 0.0
        if a < len(feature_names) and b < len(feature_names):
            scores.append(
                InteractionScore(
                    feature_a=feature_names[a],
                    feature_b=feature_names[b],
                    score=round(min(1.0, score), 4),
                )
            )
    return sorted(scores, key=lambda s: s.score, reverse=True)[:_TOP_INTERACTIONS]


def _walk_paths_for_cooccurrence(
    node: TreeNode,
    path: list[int],
    co: dict[tuple[int, int], int],
    splits: dict[int, int],
) -> None:
    if node.split_feature is None:
        return
    feat = node.split_feature
    splits[feat] = splits.get(feat, 0) + 1
    for ancestor in path:
        key = (min(ancestor, feat), max(ancestor, feat))
        co[key] = co.get(key, 0) + 1
    new_path = [*path, feat]
    if node.left:
        _walk_paths_for_cooccurrence(node.left, new_path, co, splits)
    if node.right:
        _walk_paths_for_cooccurrence(node.right, new_path, co, splits)


def _detect_unused(
    artifact: CerebroArtifact, feature_names: list[str]
) -> list[str]:
    used: set[int] = set()
    for tree in artifact.trees:
        _collect_used_features(tree.root, used)
    return [
        feature_names[i]
        for i in range(len(feature_names))
        if i not in used
    ]


def _collect_used_features(node: TreeNode, used: set[int]) -> None:
    if node.split_feature is not None:
        used.add(node.split_feature)
    if node.left:
        _collect_used_features(node.left, used)
    if node.right:
        _collect_used_features(node.right, used)


def _build_recommendations(
    redundancy: list[RedundancyWarning],
    leakage: list[LeakageWarning],
    interactions: list[InteractionScore],
    unused: list[str],
    gain: dict[str, float],
) -> list[Recommendation]:
    recs: list[Recommendation] = []

    for w in redundancy:
        recs.append(
            Recommendation(
                kind="drop",
                feature=w.weak_feature,
                reason=(
                    f"Redundant with {w.dominant_feature} "
                    f"(correlation={w.correlation:.2f}, "
                    f"gain_ratio={w.gain_ratio:.2f})"
                ),
                impact_estimate="low",
                details={
                    "dominant_feature": w.dominant_feature,
                    "correlation": w.correlation,
                    "gain_ratio": w.gain_ratio,
                },
            )
        )

    for w in leakage:
        recs.append(
            Recommendation(
                kind="investigate_leakage",
                feature=w.feature,
                reason=(
                    f"Gain rank={w.gain_rank} but permutation rank={w.permutation_rank} "
                    f"(delta={w.delta}); potential data leakage"
                ),
                impact_estimate="high",
                details={"gain_rank": w.gain_rank, "permutation_rank": w.permutation_rank},
            )
        )

    for u in unused:
        recs.append(
            Recommendation(
                kind="drop",
                feature=u,
                reason="Feature never appears in any tree split",
                impact_estimate="zero",
            )
        )

    for s in interactions:
        if s.score >= _STRONG_INTERACTION_THRESHOLD:
            recs.append(
                Recommendation(
                    kind="engineer_interaction",
                    feature=f"{s.feature_a}:{s.feature_b}",
                    reason=(
                        f"Strong co-occurrence in tree paths "
                        f"(interaction_score={s.score:.2f})"
                    ),
                    impact_estimate="medium",
                    details={
                        "feature_a": s.feature_a,
                        "feature_b": s.feature_b,
                        "score": s.score,
                    },
                )
            )

    impact_order = {"high": 0, "medium": 1, "low": 2, "zero": 3}
    return sorted(recs, key=lambda r: impact_order.get(r.impact_estimate, 99))
