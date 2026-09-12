CREATE TABLE follow_system (
    follow_id   BIGSERIAL PRIMARY KEY,
    follow_by   BIGINT NOT NULL REFERENCES users(id),
    follow_by_u VARCHAR(255) NOT NULL,
    follow_to   BIGINT NOT NULL REFERENCES users(id),
    follow_to_u VARCHAR(255) NOT NULL,
    time        TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (follow_by, follow_to)
);

CREATE INDEX idx_follow_system_follow_to ON follow_system(follow_to);
CREATE INDEX idx_follow_system_follow_by ON follow_system(follow_by);

CREATE TABLE profile_views (
    view_id   BIGSERIAL PRIMARY KEY,
    view_from BIGINT NOT NULL REFERENCES users(id),
    view_to   BIGINT NOT NULL REFERENCES users(id),
    time      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_profile_views_view_to ON profile_views(view_to);
