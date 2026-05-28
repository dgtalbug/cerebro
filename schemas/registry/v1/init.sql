-- Cerebro registry schema v1.
-- The registry is a DERIVED INDEX over .cerebro.json files; it holds metadata
-- pointing at files, never canonical data. Rebuildable via `cerebro index`.
-- This file is a committed contract: scripts/check_contracts.py asserts it
-- applies cleanly, and that the live registry schema matches it.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;
PRAGMA synchronous = NORMAL;

CREATE TABLE IF NOT EXISTS artifacts (
    id              TEXT PRIMARY KEY,            -- short hash of content (e.g. 'a3f9b21')
    name            TEXT NOT NULL,               -- file basename without extension
    path            TEXT NOT NULL UNIQUE,        -- absolute path to .cerebro.json
    framework       TEXT NOT NULL,               -- 'lightgbm'
    framework_ver   TEXT NOT NULL,
    objective       TEXT NOT NULL,               -- 'binary' | 'multiclass' | 'regression' | 'lambdarank' | ...
    num_class       INTEGER NOT NULL DEFAULT 1,
    num_trees       INTEGER NOT NULL,
    num_features    INTEGER NOT NULL,
    schema_version  TEXT NOT NULL,               -- '1.0.0'
    extractor_ver   TEXT NOT NULL,
    extracted_at    TEXT NOT NULL,               -- ISO-8601 UTC
    has_shap        INTEGER NOT NULL DEFAULT 0,  -- 0/1
    has_evaluation  INTEGER NOT NULL DEFAULT 0,  -- 0/1
    size_bytes      INTEGER NOT NULL,
    content_sha256  TEXT NOT NULL,               -- full hash; id is the short form
    registered_at   TEXT NOT NULL,               -- when this row was inserted
    last_seen_at    TEXT NOT NULL                -- last time the file was confirmed on disk
);

CREATE INDEX IF NOT EXISTS idx_artifacts_framework ON artifacts(framework);
CREATE INDEX IF NOT EXISTS idx_artifacts_objective ON artifacts(objective);
CREATE INDEX IF NOT EXISTS idx_artifacts_extracted_at ON artifacts(extracted_at);
CREATE INDEX IF NOT EXISTS idx_artifacts_name ON artifacts(name);

CREATE TABLE IF NOT EXISTS tags (
    artifact_id     TEXT NOT NULL,
    tag             TEXT NOT NULL,
    PRIMARY KEY (artifact_id, tag),
    FOREIGN KEY (artifact_id) REFERENCES artifacts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_tags_tag ON tags(tag);

CREATE TABLE IF NOT EXISTS validation_runs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_id     TEXT NOT NULL,
    ran_at          TEXT NOT NULL,
    schema_version  TEXT NOT NULL,
    passed          INTEGER NOT NULL,            -- 0/1
    checks_total    INTEGER NOT NULL,
    checks_passed   INTEGER NOT NULL,
    warnings        INTEGER NOT NULL DEFAULT 0,
    errors          INTEGER NOT NULL DEFAULT 0,
    details_json    TEXT NOT NULL,               -- structured check results
    FOREIGN KEY (artifact_id) REFERENCES artifacts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_validation_artifact ON validation_runs(artifact_id);

-- Registry's own version, used for future migrations.
CREATE TABLE IF NOT EXISTS registry_meta (
    key             TEXT PRIMARY KEY,
    value           TEXT NOT NULL
);

INSERT OR IGNORE INTO registry_meta(key, value) VALUES ('registry_version', '1.0.0');
