"""
Notification component: business logic sitting on top of app/queries/notify.py.

Ported from a PHP `notifications` class that echoed HTML directly and pulled
the viewer id from $_SESSION. This version returns structured data instead of
HTML (rendering belongs in a Jinja2 template, matching app/templates/) and
takes the viewer id as an explicit argument, matching the rest of this
codebase's dependency style.

Two notification types from the original PHP (`grp_con`, `changeGrpConAdmin`)
referenced a group-conversation/messaging feature that has no backing table
in this project (see the deleted app/queries/msg.py). They're preserved as
recognized types but are not resolved to a conversation name below.
"""

import asyncpg

from app.queries import follows as follows_q
from app.queries import groups as groups_q
from app.queries import notify as notify_q
from app.queries import users as users_q

_GROUP_TYPES = {"grp_add", "inviteGrp", "changeGrpAdmin"}


def unread_badge(count: int) -> str | None:
    if count <= 0:
        return None
    if count < 9:
        return str(count)
    return "+"


async def title_noti(conn: asyncpg.Connection, user_id: int) -> str | None:
    count = await notify_q.count_unread(conn, user_id)
    badge = unread_badge(count)
    return f"({badge})" if badge else None


async def mark_read(conn: asyncpg.Connection, user_id: int) -> None:
    await notify_q.mark_all_read(conn, user_id)


async def clear_notifications(conn: asyncpg.Connection, user_id: int) -> None:
    await notify_q.clear_notifications(conn, user_id)


async def follow_notify(conn: asyncpg.Connection, by: int, to: int) -> None:
    await notify_q.create_notification(conn, notify_by=by, notify_to=to, type_="follow")


async def recommend_notify(conn: asyncpg.Connection, by: int, to: int, of: int) -> None:
    await notify_q.create_notification(
        conn, notify_by=by, notify_to=to, type_="recommend", notify_of=of
    )


async def action_notify(
    conn: asyncpg.Connection, by: int, to: int, post_id: int, type_: str
) -> None:
    if by == to:
        return
    await notify_q.create_notification(
        conn, notify_by=by, notify_to=to, type_=type_, post_id=post_id
    )


async def comment_like_notify(
    conn: asyncpg.Connection, by: int, to: int, post_id: int, comment_id: int
) -> None:
    await notify_q.create_notification(
        conn, notify_by=by, notify_to=to, type_="commentLike", post_id=post_id, comment_id=comment_id,
    )


async def get_notifications(
    conn: asyncpg.Connection, user_id: int, before_id: int | None = None, limit: int = 10
) -> list[dict]:
    rows = await notify_q.list_notifications(conn, user_id, before_id, limit)

    user_cache: dict[int, asyncpg.Record | None] = {}
    group_cache: dict[int, asyncpg.Record | None] = {}

    async def get_user(uid: int | None):
        if uid is None:
            return None
        if uid not in user_cache:
            user_cache[uid] = await users_q.get_user_by_id(conn, uid)
        return user_cache[uid]

    async def get_group(gid: int | None):
        if gid is None:
            return None
        if gid not in group_cache:
            group_cache[gid] = await groups_q.get_group_by_id(conn, gid)
        return group_cache[gid]

    notifications = []
    for row in rows:
        by_user = await get_user(row["notify_by"])
        of_user = await get_user(row["notify_of"])

        entry = {
            "id": row["noti_id"],
            "type": row["type"],
            "status": row["status"],
            "time": row["time"],
            "by": dict(by_user) if by_user else None,
            "of": dict(of_user) if of_user else None,
            "post_id": row["post_id"],
            "comment_id": row["comment_id"],
            "group": None,
            "viewer_follows_by": False,
            "viewer_follows_of": False,
        }

        if by_user is not None:
            status = await follows_q.get_follow_status(conn, user_id, by_user["id"])
            entry["viewer_follows_by"] = status == "accepted"

        if of_user is not None:
            status = await follows_q.get_follow_status(conn, user_id, of_user["id"])
            entry["viewer_follows_of"] = status == "accepted"

        if row["type"] in _GROUP_TYPES and row["post_id"] is not None:
            group = await get_group(row["post_id"])
            entry["group"] = dict(group) if group else None

        notifications.append(entry)

    return notifications
