CREATE EXTENSION IF NOT EXISTS vector;

-- Explicaciones generadas por el Explainer
CREATE TABLE explanations (
    id                TEXT PRIMARY KEY,
    source_key        TEXT NOT NULL,
    result            JSONB NOT NULL,
    report            JSONB,
    duration_ms       INTEGER,
    feedback          TEXT CHECK (feedback IN ('up', 'down')),
    feedback_at       TIMESTAMPTZ,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    augmented_result  JSONB
);

CREATE INDEX ON explanations (source_key);
CREATE INDEX ON explanations (created_at DESC);
CREATE INDEX ON explanations (feedback);
CREATE INDEX ON explanations USING gin (result);
CREATE INDEX ON explanations ((result #>> '{0,event_metadata,severity}'));
CREATE INDEX ON explanations ((result #>> '{0,rag_search_parameters,anomaly_type}'));

CREATE TABLE documents (
    id          SERIAL PRIMARY KEY,
    title       TEXT,
    content     TEXT NOT NULL,
    embedding   VECTOR(1536),
    source      TEXT,
    created_at  TIMESTAMPTZ DEFAULT now()
);
