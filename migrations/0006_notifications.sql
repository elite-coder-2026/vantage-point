CREATE TABLE notifications (
    noti_id     BIGSERIAL PRIMARY KEY,
    notify_by   BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notify_to   BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    notify_of   BIGINT REFERENCES users(id) ON DELETE CASCADE,
    post_id     BIGINT REFERENCES posts(id) ON DELETE CASCADE,
    comment_id  BIGINT,
    type        VARCHAR(32) NOT NULL,
    status      VARCHAR(16) NOT NULL DEFAULT 'unread',
    time        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_notifications_notify_to ON notifications(notify_to, noti_id DESC);
