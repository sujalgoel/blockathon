CREATE TABLE IF NOT EXISTS verifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    applicant_id TEXT NOT NULL,
    overall_confidence INTEGER NOT NULL,
    is_verified INTEGER NOT NULL,
    tx_hash TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    verification_id INTEGER NOT NULL REFERENCES verifications(id),
    doc_type TEXT NOT NULL,
    original_size INTEGER NOT NULL,
    compressed_size INTEGER NOT NULL,
    fields_json TEXT NOT NULL,
    compressed_url TEXT
);

CREATE TABLE IF NOT EXISTS cross_validation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    verification_id INTEGER NOT NULL REFERENCES verifications(id),
    field TEXT NOT NULL,
    status TEXT NOT NULL,
    documents_json TEXT NOT NULL,
    values_json TEXT NOT NULL
);
