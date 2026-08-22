-- AI-Connex Production Database Initialization Schema
-- Level 2: Durable State & Infrastructure

CREATE TABLE IF NOT EXISTS tenants (
    tenant_id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100) DEFAULT 'industrial',
    tier VARCHAR(50) DEFAULT 'professional',
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dataset_schemas (
    asset_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(100) REFERENCES tenants(tenant_id),
    asset_name VARCHAR(255) NOT NULL,
    storage_uri TEXT NOT NULL,
    format VARCHAR(32) NOT NULL,
    size_bytes BIGINT NOT NULL,
    sha256_hash CHAR(64) NOT NULL,
    schema_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS run_logs (
    run_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(100) REFERENCES tenants(tenant_id),
    dag_id VARCHAR(64) NOT NULL,
    status VARCHAR(32) DEFAULT 'QUEUED',
    metrics JSONB,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Default system tenant
INSERT INTO tenants (tenant_id, name, industry, status)
VALUES ('default-tenant', 'Default Industrial Site', 'industrial', 'active')
ON CONFLICT (tenant_id) DO NOTHING;
