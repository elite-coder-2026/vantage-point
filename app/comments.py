"""
Comment component: business logic sitting on top of app/queries/comments.py.

Ported from the `postComment` calls referenced throughout post.php
(`getComments`, `simpleGetComments`, `comments`). Those weren't provided as
a standalone class, so this is a minimal reconstruction covering what
post.php actually calls: listing and counting a post's comments, plus
create/delete since a comment feed is useless without them. Notifies the
post's author on a new comment (skipped when the author is commenting on
their own post), matching app/notify.py's action_notify convention used
for likes and tags.
"""

import asyncpg

from app import notify as notify_svc
from app.queries import comments as comments_q
from app.queries import posts as posts_q


async def create_comment(conn: asyncpg.Connection, post_id: int, user_id: int, body: str) -> dict:
    row = await comments_q.create_comment(conn, post_id, user_id, body)
    author_id = await posts_q.get_post_author(conn, post_id)
    if author_id is not None:
        await notify_svc.action_notify(conn, by=user_id, to=author_id, post_id=post_id, type_="comment")
    return dict(row)


async def delete_comment(conn: asyncpg.Connection, comment_id: int, user_id: int) -> bool:
    return await comments_q.delete_comment(conn, comment_id, user_id) is not None


async def get_comments(
    conn: asyncpg.Connection, viewer_id: int | None, post_id: int, limit: int = 20, before_id: int | None = None,
) -> list[dict]:
    rows = await comments_q.list_comments(conn, viewer_id, post_id, limit, before_id)
    return [dict(r) for r in rows]


async def simple_get_comments(conn: asyncpg.Connection, post_id: int) -> int:
    return await comments_q.count_comments(conn, post_id)
