ALTER TABLE users ADD COLUMN type VARCHAR(32) NOT NULL DEFAULT 'general';

CREATE TABLE email_private (
    user_id     BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    options     VARCHAR(16) NOT NULL DEFAULT 'public'
);

CREATE TABLE mobile_private (
    user_id     BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    options     VARCHAR(16) NOT NULL DEFAULT 'public'
);

CREATE TABLE block (
    id          BIGSERIAL PRIMARY KEY,
    block_by    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    block_to    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    time        TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT no_self_block CHECK (block_by <> block_to),
    CONSTRAINT uq_block_pair UNIQUE (block_by, block_to)
);
CREATE INDEX idx_block_by ON block(block_by);
CREATE INDEX idx_block_to ON block(block_to);

CREATE TABLE login_history (
    id          BIGSERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    time        TIMESTAMPTZ NOT NULL DEFAULT now(),
    os          TEXT,
    browser     TEXT,
    ip          TEXT,
    logout_time TIMESTAMPTZ
);
CREATE INDEX idx_login_history_user ON login_history(user_id, time DESC);
