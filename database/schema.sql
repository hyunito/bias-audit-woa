
CREATE TABLE IF NOT EXISTS provenance_logs (
    id SERIAL PRIMARY KEY,
    operation VARCHAR(255) NOT NULL,
    by_whom VARCHAR(255) DEFAULT 'system',
    timestamp TIMESTAMP NOT NULL,
    metadata JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_provenance_metadata ON provenance_logs USING GIN (metadata);
