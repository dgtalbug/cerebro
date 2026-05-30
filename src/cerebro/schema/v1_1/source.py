"""Source metadata for a canonical artifact.

The `framework` literal is widened in v1.1.0 to include XGBoost.
v1.0.0 artifacts with framework="lightgbm" continue to validate unchanged.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class Source(BaseModel):
    """Where this artifact came from and when."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    framework: Literal["lightgbm", "xgboost"]
    framework_version: str
    extracted_at: str
    extractor_version: str
