ALTER TABLE posts ADD COLUMN type VARCHAR(16) NOT NULL DEFAULT 'text';
ALTER TABLE posts ADD COLUMN font_size INT;
ALTER TABLE posts ADD COLUMN address TEXT;

ALTER TABLE users ADD COLUMN avatar_path TEXT;

CREATE TABLE post_images (
    post_id     BIGINT PRIMARY KEY REFERENCES posts(id) ON DELETE CASCADE,
    path        TEXT NOT NULL,
    filter      VARCHAR(32)
);

CREATE TABLE post_videos (
    post_id     BIGINT PRIMARY KEY REFERENCES posts(id) ON DELETE CASCADE,
    path        TEXT NOT NULL
);

CREATE TABLE post_audios (
    post_id     BIGINT PRIMARY KEY REFERENCES posts(id) ON DELETE CASCADE,
    path        TEXT NOT NULL
);

CREATE TABLE post_documents (
    post_id     BIGINT PRIMARY KEY REFERENCES posts(id) ON DELETE CASCADE,
    path        TEXT NOT NULL
);

CREATE TABLE post_locations (
    post_id     BIGINT PRIMARY KEY REFERENCES posts(id) ON DELETE CASCADE,
    image_url   TEXT NOT NULL
);

CREATE TABLE post_links (
    post_id     BIGINT PRIMARY KEY REFERENCES posts(id) ON DELETE CASCADE,
    url         TEXT NOT NULL,
    title       TEXT,
    image_url   TEXT
);

CREATE TABLE post_likes (
    id          BIGSERIAL PRIMARY KEY,
    post_id     BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (post_id, user_id)
);
CREATE INDEX idx_post_likes_post ON post_likes(post_id);

CREATE TABLE post_comments (
    id          BIGSERIAL PRIMARY KEY,
    post_id     BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    body        TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at  TIMESTAMPTZ
);
CREATE INDEX idx_post_comments_post ON post_comments(post_id, created_at);

CREATE TABLE comment_likes (
    id          BIGSERIAL PRIMARY KEY,
    comment_id  BIGINT NOT NULL REFERENCES post_comments(id) ON DELETE CASCADE,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (comment_id, user_id)
);

CREATE TABLE post_shares (
    id          BIGSERIAL PRIMARY KEY,
    post_id     BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    share_by    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    share_to    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT no_self_share CHECK (share_by <> share_to)
);
CREATE INDEX idx_post_shares_to ON post_shares(share_to, id DESC);
CREATE INDEX idx_post_shares_post ON post_shares(post_id);

CREATE TABLE post_taggings (
    id              BIGSERIAL PRIMARY KEY,
    post_id         BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    tagged_user_id  BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (post_id, tagged_user_id)
);
CREATE INDEX idx_post_taggings_user ON post_taggings(tagged_user_id, id DESC);

CREATE TABLE post_mentions (
    id                  BIGSERIAL PRIMARY KEY,
    post_id             BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    mentioned_user_id   BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (post_id, mentioned_user_id)
);
