"""Filesystem storage for canonical artifacts.

The artifact file is the source of truth (project invariant #1 / #4).
The future SQLite registry under this package will be a derived index
of metadata pointing at these files; deleting the DB always rebuilds
from `read_artifact` over the artifacts directory.
"""

from cerebro.storage.files import read_artifact, write_artifact

__all__ = ["read_artifact", "write_artifact"]
