"""Extractor protocol — the single seam between framework code and canonical JSON.

Every framework-aware extractor (LightGBM today; XGBoost, CatBoost later)
implements this protocol. Downstream layers (storage, API, dashboard, agent)
never depend on a framework; they consume `CerebroArtifact` only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from cerebro.schema import CerebroArtifact


@runtime_checkable
class Extractor(Protocol):
    """Build a CerebroArtifact from a framework-native model file."""

    def extract(self, model_path: str | Path) -> CerebroArtifact: ...
