
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS claimants (
    claimant_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    phone TEXT NOT NULL,
    address_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS providers (
    provider_id TEXT PRIMARY KEY,
    provider_name TEXT NOT NULL,
    provider_type TEXT NOT NULL,
    tax_id TEXT NOT NULL,
    address_id TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS policies (
    policy_id TEXT PRIMARY KEY,
    claimant_id TEXT NOT NULL,
    policy_type TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    coverage_limit REAL NOT NULL CHECK (coverage_limit > 0),
    status TEXT NOT NULL,
    FOREIGN KEY (claimant_id) REFERENCES claimants(claimant_id),
    CHECK (start_date <= end_date)
);

CREATE TABLE IF NOT EXISTS incidents (
    incident_id TEXT PRIMARY KEY,
    incident_date TEXT NOT NULL,
    incident_type TEXT NOT NULL,
    location TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id TEXT PRIMARY KEY,
    claimant_id TEXT NOT NULL,
    policy_id TEXT NOT NULL,
    incident_id TEXT NOT NULL,
    provider_id TEXT NOT NULL,
    claim_date TEXT NOT NULL,
    claimed_amount REAL NOT NULL CHECK (claimed_amount > 0),
    approved_amount REAL NOT NULL CHECK (
        approved_amount >= 0 AND approved_amount <= claimed_amount
    ),
    status TEXT NOT NULL,
    FOREIGN KEY (claimant_id) REFERENCES claimants(claimant_id),
    FOREIGN KEY (policy_id) REFERENCES policies(policy_id),
    FOREIGN KEY (incident_id) REFERENCES incidents(incident_id),
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id)
);

CREATE TABLE IF NOT EXISTS invoices (
    invoice_id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL UNIQUE,
    provider_id TEXT NOT NULL,
    invoice_amount REAL NOT NULL CHECK (invoice_amount > 0),
    invoice_date TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id),
    FOREIGN KEY (provider_id) REFERENCES providers(provider_id)
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL,
    invoice_id TEXT NOT NULL,
    payment_amount REAL NOT NULL CHECK (payment_amount > 0),
    payment_date TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (claim_id) REFERENCES claims(claim_id),
    FOREIGN KEY (invoice_id) REFERENCES invoices(invoice_id)
);

CREATE TABLE IF NOT EXISTS relationship_edges (
    edge_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    edge_type TEXT NOT NULL,
    effective_date TEXT NOT NULL,
    is_planted_suspicious INTEGER NOT NULL DEFAULT 0
        CHECK (is_planted_suspicious IN (0, 1)),
    UNIQUE (source_id, target_id, edge_type)
);

CREATE INDEX IF NOT EXISTS idx_claims_claimant
    ON claims(claimant_id);

CREATE INDEX IF NOT EXISTS idx_claims_provider
    ON claims(provider_id);

CREATE INDEX IF NOT EXISTS idx_claims_policy
    ON claims(policy_id);

CREATE INDEX IF NOT EXISTS idx_invoices_provider
    ON invoices(provider_id);

CREATE INDEX IF NOT EXISTS idx_payments_claim
    ON payments(claim_id);

CREATE INDEX IF NOT EXISTS idx_edges_source
    ON relationship_edges(source_id);

CREATE INDEX IF NOT EXISTS idx_edges_target
    ON relationship_edges(target_id);
