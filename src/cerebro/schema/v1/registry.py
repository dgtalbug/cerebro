"""Registry API response models — models, versions, ingest, and enrich.

These are consumption-layer DTOs returned by the API. They are separate from
the canonical artifact schema (artifact.py) and never imported by extraction
or storage code.
"""

from __future__ import annotations

from pydantic import BaseModel


class SectionStatus(BaseModel):
    trees: bool
    importance: bool
    shap: bool
    evaluation: bool
    data_profile: bool


class ModelSummary(BaseModel):
    """Card data for the registry home view."""

    id: str
    name: str
    description: str | None
    latest_version: int
    latest_version_date: str
    framework: str
    objective: str
    section_status: SectionStatus
    created_at: str


class VersionSummary(BaseModel):
    version: int
    artifact_id: str
    section_status: SectionStatus
    notes: str | None
    created_at: str


class ModelDetail(BaseModel):
    """Detail page data — full version history, newest first."""

    id: str
    name: str
    description: str | None
    versions: list[VersionSummary]
    created_at: str


class IngestRequest(BaseModel):
    model_name: str
    notes: str | None = None


class IngestResponse(BaseModel):
    model_id: str
    model_name: str
    version: int
    artifact_id: str
    sections: SectionStatus


class EnrichRequest(BaseModel):
    samples_path: str | None = None
    labels_path: str | None = None
    training_table_path: str | None = None


class EnrichResponse(BaseModel):
    artifact_id: str
    sections_added: list[str]
    enriched_at: str
