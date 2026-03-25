CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    user_id         VARCHAR(20) UNIQUE NOT NULL,
    username        VARCHAR(100) UNIQUE NOT NULL,
    password        VARCHAR(255) NOT NULL,
    display_name    VARCHAR(100) NOT NULL,
    country_code    VARCHAR(10),
    account_number  VARCHAR(50),
    employer        VARCHAR(100),
    designation     VARCHAR(100),
    monthly_salary  DECIMAL(12,2),
    mobile          VARCHAR(30),
    address         TEXT,
    kyc_status      VARCHAR(30) DEFAULT 'Completed',
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS accounts (
    id               SERIAL PRIMARY KEY,
    user_id          VARCHAR(20) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    type             VARCHAR(50) NOT NULL,
    balance          DECIMAL(12,2) DEFAULT 0,
    account_number   VARCHAR(50) NOT NULL,
    account_type     VARCHAR(100),
    account_status   VARCHAR(30) DEFAULT 'Active',
    branch_code      VARCHAR(50),
    currency         VARCHAR(10) DEFAULT 'SAR',
    instrument_type  VARCHAR(50),
    instrument_id    VARCHAR(50),
    per_txn_limit    DECIMAL(12,2),
    daily_limit      DECIMAL(12,2),
    monthly_limit    DECIMAL(12,2),
    available_credit DECIMAL(12,2),
    created_at       TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions (
    id              SERIAL PRIMARY KEY,
    user_id         VARCHAR(20) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    txn_id          VARCHAR(20) NOT NULL,
    merchant        VARCHAR(100) NOT NULL,
    date            VARCHAR(20) NOT NULL,
    time            VARCHAR(10) NOT NULL,
    type            VARCHAR(30) NOT NULL,
    amount          DECIMAL(12,2) NOT NULL,
    status          VARCHAR(20) NOT NULL,
    icon            VARCHAR(30) NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS categories (
    id              SERIAL PRIMARY KEY,
    slug            VARCHAR(50) UNIQUE NOT NULL,
    name            VARCHAR(100) NOT NULL,
    icon            VARCHAR(50) NOT NULL,
    description     TEXT,
    display_order   INT DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS subcategories (
    id              SERIAL PRIMARY KEY,
    category_id     INT NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    slug            VARCHAR(50) NOT NULL,
    name            VARCHAR(100) NOT NULL,
    display_order   INT DEFAULT 0,
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW(),
    UNIQUE(category_id, slug)
);

-- Note: request_logs has been replaced by the applications table below.
-- Run scripts/migrate_applications_table.py to migrate existing data.
-- The old table is renamed to request_logs_archived during migration.

CREATE TABLE IF NOT EXISTS applications (
    id              SERIAL PRIMARY KEY,
    application_id  VARCHAR(20) UNIQUE NOT NULL,   -- e.g. LOAN-000001
    trace_id        VARCHAR(100) NOT NULL,          -- platform GUID, internal only
    user_id         VARCHAR(20),
    username        VARCHAR(100),
    display_name    VARCHAR(100),
    service_type    VARCHAR(30) NOT NULL,           -- 'loan' | 'savings' | 'stock'
    service_name    VARCHAR(100) NOT NULL,          -- Human label
    status          VARCHAR(30) NOT NULL DEFAULT 'Submitted',
    admin_comments  TEXT,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_applications_user_id    ON applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_status     ON applications(status);
CREATE INDEX IF NOT EXISTS idx_applications_created_at ON applications(created_at DESC);

CREATE TABLE IF NOT EXISTS app_config (
    key         VARCHAR(100) PRIMARY KEY,
    value       TEXT,
    description TEXT,
    updated_at  TIMESTAMP DEFAULT NOW()
);
