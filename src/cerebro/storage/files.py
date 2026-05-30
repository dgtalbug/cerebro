"""Filesystem read/write for canonical artifacts.

`.cerebro.json` files are gzip-encoded on disk despite the extension —
the gzip envelope is invisible to callers. Writes are atomic via a
sibling `.tmp` file + rename. Reads validate the canonical schema and
raise typed domain errors on any corruption.

The two-function surface (`write_artifact`, `read_artifact`) is
deliberate: anything that wants to substitute storage for tests can do
so at the FastAPI dependency layer (`api/deps.py`) rather than here.
"""

from __future__ import annotations

import gzip
from pathlib import Path
from typing import Final

import pydantic

from cerebro.exceptions import ArtifactNotFoundError, CorruptArtifactError
from cerebro.logging import get_logger
from cerebro.schema import CerebroArtifact

_LOG = get_logger(__name__)

_TMP_SUFFIX: Final[str] = ".tmp"


def write_artifact(artifact: CerebroArtifact, path: Path) -> None:
    """Write `artifact` to `path` as gzip-encoded canonical JSON.

    Atomic on POSIX (and same-volume Windows): the encoded bytes land
    in a sibling `<path><.tmp>` file first, then `Path.replace` swaps
    it into place. A crashed write leaves either the prior valid file
    or nothing — never a partial artifact.
    """
    encoded = artifact.model_dump_json().encode("utf-8")
    payload = gzip.compress(encoded)

    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + _TMP_SUFFIX)
    tmp.write_bytes(payload)
    tmp.replace(path)

    _LOG.info(
        "artifact.written",
        path=str(path),
        bytes=len(payload),
        num_trees=len(artifact.trees),
    )


def read_artifact(path: Path) -> CerebroArtifact:
    """Read `path` and return a validated `CerebroArtifact`.

    Failures map to typed domain errors so callers never see the raw
    gzip / Pydantic exceptions:

    * `ArtifactNotFoundError` — the path does not exist.
    * `CorruptArtifactError` — gzip is malformed, JSON is malformed, or
      the parsed shape fails canonical-schema validation.
    """
    if not path.exists():
        raise ArtifactNotFoundError(
            f"no artifact at {path}",
            context={"artifact_path": str(path)},
        )

    try:
        decompressed = gzip.decompress(path.read_bytes())
    except (gzip.BadGzipFile, OSError, EOFError) as original:
        raise CorruptArtifactError(
            f"could not decompress {path}",
            context={"artifact_path": str(path)},
        ) from original

    try:
        artifact = CerebroArtifact.model_validate_json(decompressed)
    except pydantic.ValidationError as original:
        raise CorruptArtifactError(
            f"artifact at {path} failed schema validation",
            context={"artifact_path": str(path)},
        ) from original

    _LOG.info(
        "artifact.read",
        path=str(path),
        num_trees=len(artifact.trees),
        num_features=len(artifact.model.feature_schema.names),
    )
    return artifact
