"""
Like component: business logic sitting on top of app/queries/likes.py.

Ported from the `postLike`/comment-like calls referenced throughout
post.php (`likedOrNot`, `getPostLikes`, `simpleGetPostLikes`). Those weren't
provided as a standalone class, so this is a minimal reconstruction covering
what post.php actually calls: toggled likes on posts and on comments, each
notifying the target's author (see app/notify.py's action_notify /
comment_like_notify, already built for exactly this).
"""

import asyncpg

from app import notify as notify_svc
from app.queries import comments as comments_q
from app.queries import likes as likes_q
from app.queries import posts as posts_q


async def like_post(conn: asyncpg.Connection, post_id: int, user_id: int) -> None:
    if await likes_q.is_post_liked(conn, post_id, user_id):
        return
    await likes_q.like_post(conn, post_id, user_id)
    author_id = await posts_q.get_post_author(conn, post_id)
    if author_id is not None:
        await notify_svc.action_notify(conn, by=user_id, to=author_id, post_id=post_id, type_="like")


async def unlike_post(conn: asyncpg.Connection, post_id: int, user_id: int) -> None:
    await likes_q.unlike_post(conn, post_id, user_id)


async def liked_or_not(conn: asyncpg.Connection, post_id: int, user_id: int) -> bool:
    return await likes_q.is_post_liked(conn, post_id, user_id)


async def get_post_likes(conn: asyncpg.Connection, post_id: int) -> int:
    return await likes_q.count_post_likes(conn, post_id)


async def like_comment(conn: asyncpg.Connection, comment_id: int, user_id: int) -> None:
    if await likes_q.is_comment_liked(conn, comment_id, user_id):
        return
    await likes_q.like_comment(conn, comment_id, user_id)
    comment = await comments_q.get_comment(conn, comment_id)
    if comment is not None:
        await notify_svc.comment_like_notify(
            conn, by=user_id, to=comment["user_id"], post_id=comment["post_id"], comment_id=comment_id,
        )


async def unlike_comment(conn: asyncpg.Connection, comment_id: int, user_id: int) -> None:
    await likes_q.unlike_comment(conn, comment_id, user_id)


async def comment_liked_or_not(conn: asyncpg.Connection, comment_id: int, user_id: int) -> bool:
    return await likes_q.is_comment_liked(conn, comment_id, user_id)
