"""Source metadata for a canonical artifact.

Identifies which framework the artifact came from and when extraction ran.
The framework field is fixed at "lightgbm" for v1.0.0; widening to other
frameworks is a future schema bump.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict


class Source(BaseModel):
    """Where this artifact came from and when."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    framework: Literal["lightgbm"]
    framework_version: str
    extracted_at: str
    extractor_version: str
