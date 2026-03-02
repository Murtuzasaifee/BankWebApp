CREATE TABLE IF NOT EXISTS users (
    id              SERIAL PRIMARY KEY,
    user_id         VARCHAR(20) UNIQUE NOT NULL,
    username        VARCHAR(100) UNIQUE NOT NULL,
    password        VARCHAR(255) NOT NULL,
    display_name    VARCHAR(100) NOT NULL,
    customer_id     VARCHAR(50),
    account_number  VARCHAR(50),
    employer        VARCHAR(100),
    designation     VARCHAR(100),
    monthly_salary  DECIMAL(12,2),
    emirates_id     VARCHAR(30),
    mobile          VARCHAR(30),
    address         TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS accounts (
    id              SERIAL PRIMARY KEY,
    user_id         VARCHAR(20) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    type            VARCHAR(50) NOT NULL,
    balance         DECIMAL(12,2) DEFAULT 0,
    number          VARCHAR(50) NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW()
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
