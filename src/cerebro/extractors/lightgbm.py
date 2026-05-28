"""LightGBM Booster -> CerebroArtifact (binary objective only).

For the frozen v1.0.0 schema only the binary classifier is supported.
Non-binary boosters raise `UnsupportedObjectiveError` before any partial
artifact is built — failing loudly is preferable to surfacing a
mis-typed artifact downstream.

The mapping from LightGBM's `Booster.dump_model()` shape to canonical
fields lives in this single module; the schema doesn't change shape if
LightGBM tweaks its dump format in a minor release.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import lightgbm as lgb

from cerebro import __version__ as _CEREBRO_VERSION
from cerebro.exceptions import CorruptArtifactError, UnsupportedObjectiveError
from cerebro.logging import get_logger
from cerebro.schema.v1 import (
    CerebroArtifact,
    FeatureSchema,
    Importance,
    Model,
    Source,
    Tree,
    TreeNode,
)

_LOG = get_logger(__name__)


def _resolve_categorical_indices(
    booster: lgb.Booster, feature_names: list[str]
) -> list[int]:
    """Resolve categorical feature indices from `Booster.params`.

    LightGBM's `categorical_feature` parameter is the canonical source. It
    can be a list of integer indices, a list of feature names, a
    comma-separated string of either, or the sentinel `"auto"`. Boosters
    trained without categorical features (`make_classification`-style
    synthetic data, for example) report nothing or `"auto"` here; that
    yields an empty list, which is the right shape for the v1.0.0 schema.
    """
    raw = booster.params.get("categorical_feature")
    if raw is None or raw == "auto" or raw == "":
        return []

    entries: list[int | str]
    if isinstance(raw, str):
        entries = [item.strip() for item in raw.split(",") if item.strip()]
    elif isinstance(raw, (list, tuple)):
        entries = list(raw)
    else:
        return []

    indices: set[int] = set()
    for entry in entries:
        if isinstance(entry, int):
            if 0 <= entry < len(feature_names):
                indices.add(entry)
            continue
        if isinstance(entry, str):
            if entry in feature_names:
                indices.add(feature_names.index(entry))
                continue
            try:
                idx = int(entry)
            except ValueError:
                continue
            if 0 <= idx < len(feature_names):
                indices.add(idx)
    return sorted(indices)


class LGBExtractor:
    """Extract a binary LightGBM booster into the canonical schema."""

    def extract(self, model_path: str | Path) -> CerebroArtifact:
        path = Path(model_path)
        booster = self._load_booster(path)
        dumped: dict[str, Any] = booster.dump_model()
        self._guard_objective(dumped)

        source = self._build_source()
        feature_schema = self._build_feature_schema(dumped, booster)
        model = Model(
            objective="binary",
            num_class=1,
            num_iteration=len(dumped.get("tree_info", [])),
            params=self._extract_params(booster),
            feature_schema=feature_schema,
        )
        trees = [self._build_tree(info) for info in dumped.get("tree_info", [])]
        importance = self._build_importance(booster, feature_schema.names)

        _LOG.info(
            "artifact.extracted",
            framework="lightgbm",
            objective="binary",
            num_trees=len(trees),
            num_features=len(feature_schema.names),
        )

        return CerebroArtifact(
            schema_version="1.0.0",
            source=source,
            model=model,
            trees=trees,
            importance=importance,
        )

    # -- load / guard ------------------------------------------------------

    @staticmethod
    def _load_booster(path: Path) -> lgb.Booster:
        try:
            return lgb.Booster(model_file=str(path))
        except (lgb.basic.LightGBMError, FileNotFoundError, OSError) as original:
            raise CorruptArtifactError(
                f"could not load LightGBM booster from {path}",
                context={"model_path": str(path)},
            ) from original

    @staticmethod
    def _guard_objective(dumped: dict[str, Any]) -> None:
        # LightGBM stores objective as "<name> <args>" (e.g. "binary sigmoid:1").
        raw = str(dumped.get("objective", ""))
        keyword = raw.split()[0] if raw else ""
        if keyword != "binary":
            raise UnsupportedObjectiveError(
                f"only the binary objective is supported; got {keyword!r}",
                context={"objective": keyword or raw},
            )

    # -- builders ----------------------------------------------------------

    @staticmethod
    def _build_source() -> Source:
        extracted_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        return Source(
            framework="lightgbm",
            framework_version=lgb.__version__,
            extracted_at=extracted_at,
            extractor_version=_CEREBRO_VERSION,
        )

    @staticmethod
    def _build_feature_schema(
        dumped: dict[str, Any], booster: lgb.Booster
    ) -> FeatureSchema:
        names: list[str] = list(dumped.get("feature_names", []))
        categorical_indices = _resolve_categorical_indices(booster, names)

        raw_monotone = dumped.get("monotone_constraints") or []
        monotone_constraints = (
            [int(value) for value in raw_monotone] if raw_monotone else [0] * len(names)
        )

        return FeatureSchema(
            names=names,
            categorical_indices=categorical_indices,
            monotone_constraints=monotone_constraints,
        )

    @staticmethod
    def _extract_params(booster: lgb.Booster) -> dict[str, Any]:
        # Booster.params holds the training-time parameter dict. Forward
        # all serializable entries; drop callables that some LightGBM
        # callback configurations leave on the dict.
        params = booster.params or {}
        return {key: value for key, value in params.items() if not callable(value)}

    @classmethod
    def _build_tree(cls, info: dict[str, Any]) -> Tree:
        # A monotonic counter assigns one id per node in traversal order.
        # LightGBM's split_index and leaf_index are independent sequences
        # and can collide; the canonical id only needs to be unique within
        # the tree, so we re-number.
        counter = [0]
        root = cls._build_node(info["tree_structure"], counter)
        return Tree(
            index=info["tree_index"],
            class_index=None,
            num_leaves=info["num_leaves"],
            root=root,
        )

    @classmethod
    def _build_node(cls, raw: dict[str, Any], counter: list[int]) -> TreeNode:
        node_id = counter[0]
        counter[0] += 1

        if "leaf_value" in raw and "split_feature" not in raw:
            return TreeNode(
                id=node_id,
                split_feature=None,
                threshold=None,
                decision_type=None,
                left=None,
                right=None,
                leaf_value=float(raw["leaf_value"]),
            )

        decision_type = raw.get("decision_type")
        if decision_type not in ("<=", "=="):
            # Defensive: if LightGBM ever emits a new operator we want to
            # know about it before silently mis-typing the artifact.
            raise CorruptArtifactError(
                f"unexpected decision_type {decision_type!r} in booster",
                context={"decision_type": str(decision_type)},
            )

        return TreeNode(
            id=node_id,
            split_feature=int(raw["split_feature"]),
            threshold=float(raw["threshold"]),
            decision_type=decision_type,
            left=cls._build_node(raw["left_child"], counter),
            right=cls._build_node(raw["right_child"], counter),
            leaf_value=None,
        )

    @staticmethod
    def _build_importance(booster: lgb.Booster, feature_names: list[str]) -> Importance:
        gain_array = booster.feature_importance(importance_type="gain")
        split_array = booster.feature_importance(importance_type="split")
        gain = {
            name: float(score)
            for name, score in zip(feature_names, gain_array, strict=False)
        }
        split = {
            name: float(score)
            for name, score in zip(feature_names, split_array, strict=False)
        }
        return Importance(gain=gain, split=split, permutation=None)
