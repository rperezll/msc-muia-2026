CREATE EXTENSION IF NOT EXISTS vector;

-- Explicaciones generadas por el Explainer
CREATE TABLE explanations (
    id          TEXT PRIMARY KEY,
    source_key  TEXT NOT NULL,
    result      JSONB NOT NULL,
    duration_ms INTEGER,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX ON explanations (source_key);
CREATE INDEX ON explanations (created_at DESC);

CREATE TABLE documents (
    id          SERIAL PRIMARY KEY,
    title       TEXT,
    content     TEXT NOT NULL,
    embedding   VECTOR(768),
    source      TEXT,
    created_at  TIMESTAMPTZ DEFAULT now()
);
