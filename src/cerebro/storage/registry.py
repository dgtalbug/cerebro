"""SQLite registry — derived index over .cerebro.json files on disk.

The database is fully rebuildable from the artifact directory tree via
`rebuild_from_files`. All SQL lives here; no other module interpolates SQL
strings or opens the database directly.

Directory convention for model/version identity:
  <artifacts_dir>/<model_name>/v<N>/<filename>.cerebro.json
`rebuild_from_files` walks this layout to reconstruct `models`,
`model_versions`, and `artifacts` without any external metadata.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from cerebro.exceptions import (
    ModelNotFoundError,
    RegistryError,
    VersionConflictError,
)
from cerebro.logging import get_logger
from cerebro.schema.v1.registry import (
    ModelDetail,
    ModelSummary,
    SectionStatus,
    VersionSummary,
)

_LOG = get_logger(__name__)

_SCHEMA_DIR = Path(__file__).parent.parent.parent.parent / "schemas" / "registry" / "v2"
_VERSION_DIR_RE = re.compile(r"^v(\d+)$")

# Shared write-serialisation lock — SQLite is single-writer even in WAL mode.
_write_lock = asyncio.Lock()


# ---------------------------------------------------------------------------
# Internal dataclasses (storage layer only — not exposed as API responses)
# ---------------------------------------------------------------------------


@dataclass
class _Model:
    id: str
    name: str
    description: str | None
    created_at: str


@dataclass
class _ModelVersion:
    id: str
    model_id: str
    version: int
    artifact_id: str
    notes: str | None
    created_at: str


@dataclass
class RebuildReport:
    models_created: int = 0
    versions_created: int = 0
    artifacts_registered: int = 0
    skipped_paths: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Connection helpers
# ---------------------------------------------------------------------------


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def _init_db(db_path: Path) -> None:
    sql = (_SCHEMA_DIR / "init.sql").read_text()
    conn = _connect(db_path)
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()


def _drop_all(db_path: Path) -> None:
    conn = _connect(db_path)
    try:
        conn.executescript(
            """
            PRAGMA foreign_keys = OFF;
            DROP TABLE IF EXISTS validation_runs;
            DROP TABLE IF EXISTS tags;
            DROP TABLE IF EXISTS model_versions;
            DROP TABLE IF EXISTS artifacts;
            DROP TABLE IF EXISTS models;
            DROP TABLE IF EXISTS registry_meta;
            PRAGMA foreign_keys = ON;
            """
        )
        conn.commit()
    finally:
        conn.close()


def _now() -> str:
    return (
        datetime.now(UTC)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


def _short_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()[:7]


def _full_hash(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _section_status(row: sqlite3.Row | dict[str, Any]) -> SectionStatus:
    if isinstance(row, sqlite3.Row):
        row = dict(row)
    return SectionStatus(
        trees=True,
        importance=True,
        shap=bool(row.get("has_shap", 0)),
        evaluation=bool(row.get("has_evaluation", 0)),
        data_profile=bool(row.get("has_data_profile", 0)),
    )


# ---------------------------------------------------------------------------
# Registry class
# ---------------------------------------------------------------------------


class Registry:
    """All database access for the Cerebro registry.

    Pass `db_path` to open an existing (or new) database. Call `init()` to
    ensure the schema exists.
    """

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def init(self) -> None:
        _init_db(self._db_path)

    def _conn(self) -> sqlite3.Connection:
        return _connect(self._db_path)

    # ------------------------------------------------------------------
    # Model CRUD
    # ------------------------------------------------------------------

    def register_model(self, name: str, description: str | None = None) -> _Model:
        model_id = str(uuid.uuid4())
        now = _now()
        conn = self._conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                "SELECT id, name, description, created_at FROM models WHERE name = ?",
                (name,),
            ).fetchone()
            if existing:
                conn.rollback()
                return _Model(**dict(existing))
            conn.execute(
                "INSERT INTO models (id, name, description, created_at)"
                " VALUES (?, ?, ?, ?)",
                (model_id, name, description, now),
            )
            conn.commit()
            _LOG.info("registry.model_created", model_id=model_id, name=name)
            return _Model(
                id=model_id, name=name, description=description, created_at=now
            )
        except sqlite3.Error as exc:
            conn.rollback()
            raise RegistryError(
                "failed to register model", context={"name": name}
            ) from exc
        finally:
            conn.close()

    def get_model(self, model_id: str) -> _Model | None:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT id, name, description, created_at FROM models WHERE id = ?",
                (model_id,),
            ).fetchone()
            return _Model(**dict(row)) if row else None
        finally:
            conn.close()

    def get_model_by_name(self, name: str) -> _Model | None:
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT id, name, description, created_at FROM models WHERE name = ?",
                (name,),
            ).fetchone()
            return _Model(**dict(row)) if row else None
        finally:
            conn.close()

    def list_models(
        self,
        offset: int = 0,
        limit: int = 50,
        framework: str | None = None,
        objective: str | None = None,
    ) -> list[ModelSummary]:
        """Return models with their latest-version summary."""
        conn = self._conn()
        try:
            where_clauses: list[str] = []
            params: list[Any] = []
            if framework:
                where_clauses.append("a.framework = ?")
                params.append(framework)
            if objective:
                where_clauses.append("a.objective = ?")
                params.append(objective)

            where_sql = (
                "WHERE " + " AND ".join(where_clauses)
            ) if where_clauses else ""

            # Latest version per model via correlated subquery
            sql = f"""
                SELECT
                    m.id, m.name, m.description, m.created_at,
                    mv.version AS latest_version,
                    mv.created_at AS latest_version_date,
                    a.framework, a.objective,
                    a.has_shap, a.has_evaluation, a.has_data_profile
                FROM models m
                JOIN model_versions mv ON mv.model_id = m.id
                    AND mv.version = (
                        SELECT MAX(v2.version) FROM model_versions v2
                        WHERE v2.model_id = m.id
                    )
                JOIN artifacts a ON a.id = mv.artifact_id
                {where_sql}
                ORDER BY m.created_at DESC
                LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])
            rows = conn.execute(sql, params).fetchall()
            return [
                ModelSummary(
                    id=r["id"],
                    name=r["name"],
                    description=r["description"],
                    latest_version=r["latest_version"],
                    latest_version_date=r["latest_version_date"],
                    framework=r["framework"],
                    objective=r["objective"],
                    section_status=_section_status(r),
                    created_at=r["created_at"],
                )
                for r in rows
            ]
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Version management
    # ------------------------------------------------------------------

    def create_version(
        self,
        model_id: str,
        artifact_id: str,
        notes: str | None = None,
    ) -> _ModelVersion:
        version_id = str(uuid.uuid4())
        now = _now()
        conn = self._conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT COALESCE(MAX(version), 0) AS max_v"
                " FROM model_versions WHERE model_id = ?",
                (model_id,),
            ).fetchone()
            next_version = (row["max_v"] if row else 0) + 1
            conn.execute(
                """
                INSERT INTO model_versions
                    (id, model_id, version, artifact_id, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (version_id, model_id, next_version, artifact_id, notes, now),
            )
            conn.commit()
            _LOG.info(
                "registry.version_created",
                model_id=model_id,
                version=next_version,
                artifact_id=artifact_id,
            )
            return _ModelVersion(
                id=version_id,
                model_id=model_id,
                version=next_version,
                artifact_id=artifact_id,
                notes=notes,
                created_at=now,
            )
        except sqlite3.IntegrityError as exc:
            conn.rollback()
            raise VersionConflictError(
                "concurrent version creation conflict",
                context={"model_id": model_id},
            ) from exc
        except sqlite3.Error as exc:
            conn.rollback()
            raise RegistryError(
                "failed to create version",
                context={"model_id": model_id},
            ) from exc
        finally:
            conn.close()

    def list_versions(self, model_id: str) -> list[VersionSummary]:
        conn = self._conn()
        try:
            rows = conn.execute(
                """
                SELECT mv.version, mv.artifact_id, mv.notes, mv.created_at,
                       a.has_shap, a.has_evaluation, a.has_data_profile
                FROM model_versions mv
                JOIN artifacts a ON a.id = mv.artifact_id
                WHERE mv.model_id = ?
                ORDER BY mv.version DESC
                """,
                (model_id,),
            ).fetchall()
            return [
                VersionSummary(
                    version=r["version"],
                    artifact_id=r["artifact_id"],
                    section_status=_section_status(r),
                    notes=r["notes"],
                    created_at=r["created_at"],
                )
                for r in rows
            ]
        finally:
            conn.close()

    def get_latest_version(self, model_id: str) -> _ModelVersion | None:
        conn = self._conn()
        try:
            row = conn.execute(
                """
                SELECT id, model_id, version, artifact_id, notes, created_at
                FROM model_versions
                WHERE model_id = ?
                ORDER BY version DESC
                LIMIT 1
                """,
                (model_id,),
            ).fetchone()
            return _ModelVersion(**dict(row)) if row else None
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Artifact registration
    # ------------------------------------------------------------------

    def register_artifact(
        self,
        *,
        path: Path,
        framework: str,
        framework_ver: str,
        objective: str,
        num_class: int,
        num_trees: int,
        num_features: int,
        schema_version: str,
        extractor_ver: str,
        extracted_at: str,
        has_shap: bool,
        has_evaluation: bool,
        has_data_profile: bool,
        size_bytes: int,
        content_sha256: str,
    ) -> str:
        artifact_id = content_sha256[:7]
        now = _now()
        conn = self._conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                """
                INSERT INTO artifacts (
                    id, path, framework, framework_ver, objective,
                    num_class, num_trees, num_features,
                    schema_version, extractor_ver, extracted_at,
                    has_shap, has_evaluation, has_data_profile,
                    size_bytes, content_sha256,
                    registered_at, last_seen_at
                ) VALUES (
                    ?, ?, ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?, ?,
                    ?, ?,
                    ?, ?
                )
                ON CONFLICT(id) DO UPDATE SET last_seen_at = excluded.last_seen_at
                """,
                (
                    artifact_id, str(path), framework, framework_ver, objective,
                    num_class, num_trees, num_features,
                    schema_version, extractor_ver, extracted_at,
                    int(has_shap), int(has_evaluation), int(has_data_profile),
                    size_bytes, content_sha256,
                    now, now,
                ),
            )
            conn.commit()
            return artifact_id
        except sqlite3.Error as exc:
            conn.rollback()
            raise RegistryError(
                "failed to register artifact", context={"path": str(path)}
            ) from exc
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Enrichment
    # ------------------------------------------------------------------

    def update_artifact_sections(
        self,
        artifact_id: str,
        *,
        has_shap: bool | None = None,
        has_evaluation: bool | None = None,
        has_data_profile: bool | None = None,
        content_sha256: str | None = None,
        size_bytes: int | None = None,
        enriched_at: str | None = None,
    ) -> None:
        updates: list[str] = []
        params: list[Any] = []
        if has_shap is not None:
            updates.append("has_shap = ?")
            params.append(int(has_shap))
        if has_evaluation is not None:
            updates.append("has_evaluation = ?")
            params.append(int(has_evaluation))
        if has_data_profile is not None:
            updates.append("has_data_profile = ?")
            params.append(int(has_data_profile))
        if content_sha256 is not None:
            updates.append("content_sha256 = ?")
            params.append(content_sha256)
        if size_bytes is not None:
            updates.append("size_bytes = ?")
            params.append(size_bytes)
        if enriched_at is not None:
            updates.append("enriched_at = ?")
            params.append(enriched_at)
        updates.append("last_seen_at = ?")
        params.append(_now())
        params.append(artifact_id)

        conn = self._conn()
        try:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute(
                f"UPDATE artifacts SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            conn.commit()
        except sqlite3.Error as exc:
            conn.rollback()
            raise RegistryError(
                "failed to update artifact sections",
                context={"artifact_id": artifact_id},
            ) from exc
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Model detail
    # ------------------------------------------------------------------

    def get_artifact_row(self, artifact_id: str) -> dict[str, Any] | None:
        """Return the raw artifact row as a dict, or None if not found."""
        conn = self._conn()
        try:
            row = conn.execute(
                "SELECT * FROM artifacts WHERE id = ?", (artifact_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_model_detail(self, model_id: str) -> ModelDetail:
        model = self.get_model(model_id)
        if model is None:
            raise ModelNotFoundError(
                f"no model with id {model_id!r}",
                context={"model_id": model_id},
            )
        versions = self.list_versions(model_id)
        return ModelDetail(
            id=model.id,
            name=model.name,
            description=model.description,
            versions=versions,
            created_at=model.created_at,
        )

    # ------------------------------------------------------------------
    # Rebuild from files
    # ------------------------------------------------------------------

    def rebuild_from_files(self, artifacts_dir: Path) -> RebuildReport:
        """Drop all tables, reinitialise from v2 schema, rescan the directory tree.

        Expects the layout: <artifacts_dir>/<model_name>/v<N>/<file>.cerebro.json
        Files not matching this pattern are skipped with a warning.
        """
        import gzip

        from cerebro.schema.v1 import CerebroArtifact

        _drop_all(self._db_path)
        _init_db(self._db_path)

        report = RebuildReport()
        model_cache: dict[str, str] = {}  # name -> id

        if not artifacts_dir.exists():
            _LOG.warning("rebuild.artifacts_dir_missing", path=str(artifacts_dir))
            return report

        for cerebro_file in sorted(artifacts_dir.rglob("*.cerebro.json")):
            parts = cerebro_file.relative_to(artifacts_dir).parts
            if len(parts) != 3:
                _LOG.warning("rebuild.skip_bad_layout", path=str(cerebro_file))
                report.skipped_paths.append(str(cerebro_file))
                continue
            model_name, version_dir, _ = parts
            m = _VERSION_DIR_RE.match(version_dir)
            if not m:
                _LOG.warning("rebuild.skip_bad_version_dir", path=str(cerebro_file))
                report.skipped_paths.append(str(cerebro_file))
                continue
            version_num = int(m.group(1))

            # Read and register artifact
            try:
                raw = gzip.decompress(cerebro_file.read_bytes())
                artifact = CerebroArtifact.model_validate_json(raw)
            except Exception:
                _LOG.warning("rebuild.skip_corrupt", path=str(cerebro_file))
                report.skipped_paths.append(str(cerebro_file))
                continue

            content = cerebro_file.read_bytes()
            raw_decompressed = gzip.decompress(content)
            sha256 = _full_hash(raw_decompressed)
            artifact_id = self.register_artifact(
                path=cerebro_file,
                framework=artifact.source.framework,
                framework_ver=artifact.source.framework_version,
                objective=artifact.model.objective,
                num_class=artifact.model.num_class,
                num_trees=artifact.model.num_iteration,
                num_features=len(artifact.model.feature_schema.names),
                schema_version=artifact.schema_version,
                extractor_ver=artifact.source.extractor_version,
                extracted_at=artifact.source.extracted_at,
                has_shap=artifact.explanations is not None,
                has_evaluation=artifact.evaluation is not None,
                has_data_profile=artifact.data_profile is not None,
                size_bytes=len(content),
                content_sha256=sha256,
            )
            report.artifacts_registered += 1

            # Ensure model row exists
            if model_name not in model_cache:
                model = self.register_model(model_name)
                model_cache[model_name] = model.id
                report.models_created += 1
            model_id = model_cache[model_name]

            # Insert version row directly (preserve exact number from directory layout)
            version_uuid = str(uuid.uuid4())
            now = _now()
            conn = self._conn()
            try:
                conn.execute("BEGIN IMMEDIATE")
                conn.execute(
                    """
                    INSERT OR IGNORE INTO model_versions
                        (id, model_id, version, artifact_id, notes, created_at)
                    VALUES (?, ?, ?, ?, NULL, ?)
                    """,
                    (version_uuid, model_id, version_num, artifact_id, now),
                )
                conn.commit()
                report.versions_created += 1
            except sqlite3.Error as exc:
                conn.rollback()
                _LOG.warning(
                    "rebuild.version_insert_failed",
                    path=str(cerebro_file),
                    error=str(exc),
                )
            finally:
                conn.close()

        _LOG.info(
            "rebuild.complete",
            models=report.models_created,
            versions=report.versions_created,
            artifacts=report.artifacts_registered,
            skipped=len(report.skipped_paths),
        )
        return report
