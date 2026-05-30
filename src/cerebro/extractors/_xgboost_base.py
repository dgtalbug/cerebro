"""Shared helper functions for all XGBoost variant extractors.

XGBoost is imported lazily — calling `_require_xgboost()` before use keeps
this module importable in environments without XGBoost installed (CI without
the [ml] optional deps).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from cerebro import __version__ as _CEREBRO_VERSION
from cerebro.exceptions import CorruptArtifactError, UnsupportedObjectiveError
from cerebro.schema.v1_1 import Importance, Tree, TreeNode
from cerebro.schema.v1_1.source import Source

if TYPE_CHECKING:
    import xgboost as xgb
else:
    xgb = None

_REGRESSION_OBJECTIVES: frozenset[str] = frozenset(
    {"reg:squarederror", "reg:squaredlogerror", "reg:logistic",
     "reg:pseudohubererror", "reg:absoluteerror", "reg:tweedie",
     "count:poisson", "survival:cox", "survival:aft"}
)
_BINARY_OBJECTIVES: frozenset[str] = frozenset(
    {"binary:logistic", "binary:logitraw", "binary:hinge"}
)
_MULTICLASS_OBJECTIVES: frozenset[str] = frozenset(
    {"multi:softmax", "multi:softprob"}
)
_ALL_OBJECTIVES: frozenset[str] = (
    _REGRESSION_OBJECTIVES | _BINARY_OBJECTIVES | _MULTICLASS_OBJECTIVES
)


def _require_xgboost() -> Any:
    """Lazily import XGBoost. Raises CorruptArtifactError if not installed."""
    global xgb
    if xgb is None:
        try:
            import xgboost as _xgb
        except ImportError as original:
            raise CorruptArtifactError(
                "XGBoost support requires the optional 'xgboost' dependency",
                context={"dependency": "xgboost"},
            ) from original
        xgb = _xgb
    return xgb


def _load_booster(path: Path) -> xgb.Booster:
    xgb_mod = _require_xgboost()
    if path.suffix.lower() in {".pkl", ".pickle"}:
        return _load_booster_from_pickle(path)
    try:
        booster = xgb_mod.Booster()
        booster.load_model(str(path))
        return cast(xgb.Booster, booster)
    except Exception as original:
        raise CorruptArtifactError(
            f"could not load XGBoost booster from {path}",
            context={"model_path": str(path)},
        ) from original


def _load_booster_from_pickle(path: Path) -> xgb.Booster:
    import pickle
    xgb_mod = _require_xgboost()
    try:
        with open(path, "rb") as fh:
            obj = pickle.load(fh)
    except Exception as original:
        raise CorruptArtifactError(
            f"could not unpickle model from {path}",
            context={"model_path": str(path)},
        ) from original
    if isinstance(obj, xgb_mod.Booster):
        return cast(xgb.Booster, obj)
    booster = getattr(obj, "get_booster", lambda: None)()
    if booster is not None and isinstance(booster, xgb_mod.Booster):
        return cast(xgb.Booster, booster)
    raise CorruptArtifactError(
        f"pickle at {path} does not contain an xgb.Booster or sklearn XGBoost estimator",
        context={"model_path": str(path), "pickled_type": type(obj).__name__},
    )


def _detect_objective(booster: xgb.Booster) -> str:
    """Extract the canonical objective keyword from a loaded booster."""
    cfg_str = booster.save_config()
    cfg = json.loads(cfg_str)
    # Navigate to learner → objective → name
    try:
        name = cfg["learner"]["objective"]["name"]
    except (KeyError, TypeError):
        name = ""
    if not name:
        raise UnsupportedObjectiveError(
            "could not detect XGBoost objective from booster config",
            context={"config_keys": list(cfg.get("learner", {}).keys())},
        )
    # Normalize: strip trailing ":default" variants xgboost sometimes adds
    name = name.split(":")[0] + (":" + name.split(":")[1] if ":" in name else "")
    if name not in _ALL_OBJECTIVES:
        raise UnsupportedObjectiveError(
            f"unsupported XGBoost objective {name!r}",
            context={"objective": name},
        )
    return name


def _get_feature_names(booster: xgb.Booster) -> list[str]:
    names = booster.feature_names
    if names:
        return list(names)
    # Fall back to f0, f1, ... using num_features from config
    cfg = json.loads(booster.save_config())
    try:
        n = int(cfg["learner"]["learner_model_param"]["num_feature"])
    except (KeyError, TypeError, ValueError):
        n = 0
    return [f"f{i}" for i in range(n)]


def _build_source() -> Source:
    xgb_mod = _require_xgboost()
    return Source(
        framework="xgboost",
        framework_version=xgb_mod.__version__,
        extracted_at=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        extractor_version=_CEREBRO_VERSION,
    )


def _build_importance(booster: xgb.Booster, feature_names: list[str]) -> Importance:
    gain_raw = booster.get_score(importance_type="gain")
    split_raw = booster.get_score(importance_type="weight")

    def _scalar(v: object) -> float:
        if isinstance(v, list):
            return float(sum(v))
        return float(v)  # type: ignore[arg-type]

    gain = {f: _scalar(gain_raw.get(f, 0.0)) for f in feature_names}
    split = {f: _scalar(split_raw.get(f, 0)) for f in feature_names}
    return Importance(gain=gain, split=split, permutation=None)


def _build_trees(
    booster: xgb.Booster,
    feature_names: list[str],
    num_class: int,
) -> list[Tree]:
    dumps = booster.get_dump(dump_format="json")
    trees: list[Tree] = []
    for raw_index, tree_json_str in enumerate(dumps):
        tree_dict = json.loads(tree_json_str)
        class_index = (raw_index % num_class) if num_class > 1 else None
        root = _parse_node(tree_dict, feature_names, [0])
        trees.append(
            Tree(
                index=raw_index,
                class_index=class_index,
                num_leaves=_count_leaves(tree_dict),
                root=root,
            )
        )
    return trees


def _parse_node(
    node: dict[str, Any],
    feature_names: list[str],
    counter: list[int],
) -> TreeNode:
    node_id = counter[0]
    counter[0] += 1

    if "leaf" in node:
        return TreeNode(
            id=node_id,
            split_feature=None,
            threshold=None,
            decision_type=None,
            left=None,
            right=None,
            leaf_value=float(node["leaf"]),
        )

    split_name = node.get("split", "")
    try:
        feature_index = feature_names.index(split_name)
    except ValueError:
        # XGBoost may use f0/f1 fallback names even when feature_names are set
        if split_name.startswith("f") and split_name[1:].isdigit():
            feature_index = int(split_name[1:])
        else:
            feature_index = 0

    threshold = float(node.get("split_condition", 0.0))
    children = {c["nodeid"]: c for c in node.get("children", [])}

    yes_id = node.get("yes")
    no_id = node.get("no")
    left_raw = children.get(yes_id) if yes_id is not None else None
    right_raw = children.get(no_id) if no_id is not None else None

    left = _parse_node(left_raw, feature_names, counter) if left_raw else TreeNode(
        id=counter[0], split_feature=None, threshold=None, decision_type=None,
        left=None, right=None, leaf_value=0.0,
    )
    if left_raw is None:
        counter[0] += 1
    right = _parse_node(right_raw, feature_names, counter) if right_raw else TreeNode(
        id=counter[0], split_feature=None, threshold=None, decision_type=None,
        left=None, right=None, leaf_value=0.0,
    )
    if right_raw is None:
        counter[0] += 1

    return TreeNode(
        id=node_id,
        split_feature=feature_index,
        threshold=threshold,
        decision_type="<=",
        left=left,
        right=right,
        leaf_value=None,
    )


def _count_leaves(node: dict[str, Any]) -> int:
    if "leaf" in node:
        return 1
    return sum(_count_leaves(c) for c in node.get("children", []))


def _is_xgboost_file(path: Path) -> bool:
    """Return True if the file looks like an XGBoost model."""
    if path.suffix.lower() in {".pkl", ".pickle"}:
        return False
    try:
        content = path.read_bytes()
        # XGBoost JSON models start with '{'
        if content.lstrip()[:1] == b"{":
            data = json.loads(content)
            return "learner" in data and "version" in data
        # XGBoost binary models start with a magic header
        return content[:4] == b"bst/" or b"xgboost" in content[:64].lower()
    except Exception:
        return False
