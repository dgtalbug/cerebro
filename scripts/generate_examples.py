#!/usr/bin/env python3
"""Generate example .cerebro.json artifacts for each LGB variant.

Trains a minimal LightGBM model for each variant using sklearn toy datasets,
extracts a canonical artifact, and writes to examples/ (tracked in git).

Usage:
    uv run python scripts/generate_examples.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import numpy as np
from sklearn.datasets import (
    make_classification,
    make_regression,
)

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "examples"


def _extract(model_path: Path, out_name: str, **kwargs: object) -> None:
    from cerebro.extractors import get_extractor
    from cerebro.storage import write_artifact

    extractor = get_extractor(model_path)
    artifact = extractor.extract(model_path, **kwargs)  # type: ignore[arg-type]
    out = OUT_DIR / f"{out_name}.cerebro.json"
    write_artifact(artifact, out)
    print(f"  wrote  {out.relative_to(ROOT)}")


def _binary() -> None:
    import lightgbm as lgb

    X, y = make_classification(n_samples=400, n_features=10, random_state=0)
    ds = lgb.Dataset(X, y)
    booster = lgb.train(
        {"objective": "binary", "num_leaves": 8, "verbosity": -1},
        ds,
        num_boost_round=10,
    )
    tmp = ROOT / "data" / "examples" / "_tmp.txt"
    booster.save_model(str(tmp))
    _extract(
        tmp,
        "binary",
        samples=X[:100].astype(float),
        labels=y[:100].astype(float),
        eval_samples=X[100:200].astype(float),
        eval_labels=y[100:200].astype(float),
    )
    tmp.unlink(missing_ok=True)


def _multiclass() -> None:
    import lightgbm as lgb

    X, y = make_classification(
        n_samples=400, n_features=10, n_classes=3, n_informative=5, random_state=1
    )
    ds = lgb.Dataset(X, y)
    booster = lgb.train(
        {"objective": "multiclass", "num_class": 3, "num_leaves": 8, "verbosity": -1},
        ds,
        num_boost_round=10,
    )
    tmp = ROOT / "data" / "examples" / "_tmp.txt"
    booster.save_model(str(tmp))
    _extract(
        tmp,
        "multiclass",
        samples=X[:100].astype(float),
        labels=y[:100].astype(float),
        eval_samples=X[100:200].astype(float),
        eval_labels=y[100:200].astype(float),
    )
    tmp.unlink(missing_ok=True)


def _regression() -> None:
    import lightgbm as lgb

    X, y = make_regression(n_samples=400, n_features=10, noise=0.1, random_state=2)
    ds = lgb.Dataset(X, y)
    booster = lgb.train(
        {"objective": "regression", "num_leaves": 8, "verbosity": -1},
        ds,
        num_boost_round=10,
    )
    tmp = ROOT / "data" / "examples" / "_tmp.txt"
    booster.save_model(str(tmp))
    _extract(
        tmp,
        "regression",
        samples=X[:100].astype(float),
        labels=y[:100].astype(float),
        eval_samples=X[100:200].astype(float),
        eval_labels=y[100:200].astype(float),
    )
    tmp.unlink(missing_ok=True)


def _ranker() -> None:
    import lightgbm as lgb

    rng = np.random.default_rng(3)
    n_queries, docs_per_q = 20, 10
    X = rng.standard_normal((n_queries * docs_per_q, 8)).astype(float)
    y = rng.integers(0, 5, n_queries * docs_per_q)
    groups = [docs_per_q] * n_queries
    ds = lgb.Dataset(X, y, group=groups)
    booster = lgb.train(
        {"objective": "lambdarank", "num_leaves": 8, "verbosity": -1},
        ds,
        num_boost_round=10,
    )
    tmp = ROOT / "data" / "examples" / "_tmp.txt"
    booster.save_model(str(tmp))
    _extract(tmp, "ranker")
    tmp.unlink(missing_ok=True)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating examples → {OUT_DIR.relative_to(ROOT)}/\n")
    _binary()
    _multiclass()
    _regression()
    _ranker()
    print(f"\nGenerated 4 example artifacts in {OUT_DIR.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
