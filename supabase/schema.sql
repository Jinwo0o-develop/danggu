-- ============================================================
-- Supabase Schema — Claude Code Harness (당근마켓)
-- SQL Editor에서 전체 실행하세요.
-- ============================================================

-- customers
CREATE TABLE IF NOT EXISTS customers (
    id              SERIAL PRIMARY KEY,
    email           TEXT UNIQUE NOT NULL,
    name            TEXT NOT NULL,
    phone           TEXT DEFAULT '',
    hashed_password TEXT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- admin_users
CREATE TABLE IF NOT EXISTS admin_users (
    id              SERIAL PRIMARY KEY,
    username        TEXT UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'operator',
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- admin_register_keys
CREATE TABLE IF NOT EXISTS admin_register_keys (
    id          SERIAL PRIMARY KEY,
    key         TEXT UNIQUE NOT NULL,
    created_by  TEXT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    used        BOOLEAN DEFAULT FALSE,
    used_by     TEXT,
    used_at     TIMESTAMPTZ,
    revoked     BOOLEAN DEFAULT FALSE
);

-- danggn_applications
CREATE TABLE IF NOT EXISTS danggn_applications (
    id                SERIAL PRIMARY KEY,
    name              TEXT NOT NULL,
    phone             TEXT NOT NULL,
    item_name         TEXT NOT NULL,
    description       TEXT NOT NULL,
    listed_price      TEXT DEFAULT '무료나눔',
    media_files       JSONB DEFAULT '[]',
    category          TEXT DEFAULT '기타',
    user_id           INTEGER,
    status            TEXT DEFAULT '접수됨',
    lookup_code       TEXT UNIQUE,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    sale_price        INTEGER,
    commission_rate   FLOAT,
    commission_amount INTEGER,
    settlement_amount INTEGER
);

-- danggn_auth_codes (phone별 최신 1개만 유지, phone이 PK)
CREATE TABLE IF NOT EXISTS danggn_auth_codes (
    phone       TEXT PRIMARY KEY,
    code        TEXT NOT NULL,
    expires_at  TIMESTAMPTZ NOT NULL,
    used        BOOLEAN DEFAULT FALSE
);

-- danggn_event_logs
CREATE TABLE IF NOT EXISTS danggn_event_logs (
    id              SERIAL PRIMARY KEY,
    application_id  INTEGER NOT NULL,
    from_status     TEXT,
    to_status       TEXT NOT NULL,
    changed_by      TEXT,
    note            TEXT DEFAULT '',
    occurred_at     TIMESTAMPTZ DEFAULT NOW()
);

-- danggn_reviews
CREATE TABLE IF NOT EXISTS danggn_reviews (
    id          SERIAL PRIMARY KEY,
    rating      TEXT NOT NULL,
    comment     TEXT DEFAULT '',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- danggn_commission_rates (category가 PK)
CREATE TABLE IF NOT EXISTS danggn_commission_rates (
    category  TEXT PRIMARY KEY,
    rate      FLOAT NOT NULL DEFAULT 0.1
);

-- 기본 요율 데이터
INSERT INTO danggn_commission_rates (category, rate) VALUES
    ('전자제품', 0.20),
    ('가구',     0.15),
    ('의류',     0.10),
    ('기타',     0.15)
ON CONFLICT (category) DO NOTHING;

-- menus (점심 메뉴 추천)
CREATE TABLE IF NOT EXISTS menus (
    id      SERIAL PRIMARY KEY,
    emoji   TEXT NOT NULL DEFAULT '',
    name    TEXT NOT NULL,
    desc    TEXT NOT NULL DEFAULT ''
);

-- danggn_settings (key-value)
CREATE TABLE IF NOT EXISTS danggn_settings (
    key    TEXT PRIMARY KEY,
    value  TEXT NOT NULL
);

-- 기본 설정 데이터
INSERT INTO danggn_settings (key, value) VALUES
    ('auto_cancel_days', '7')
ON CONFLICT (key) DO NOTHING;
