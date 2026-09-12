"""
Settings component: business logic sitting on top of app/queries/settings.py.

Ported from a PHP `Settings` class that pulled the viewer id from $_SESSION,
echoed HTML directly, and read `N.get_db()` / a `Universal` helper for raw
queries. This version returns structured data instead of HTML (rendering
belongs in a Jinja2 template, matching app/templates/) and takes the viewer
id as an explicit argument, matching the rest of this codebase's dependency
style (see app/notify.py).

The original class also called out to `Avatar.display_avatar` and
`Mutual.e_mutual` helpers when listing blocked users. Neither concept exists
in this project (no avatar or mutual-connections feature), so
`blocked_users` returns plain user rows; a caller can join in avatar/mutual
data once those features exist.
"""

import asyncpg

from app.auth import hash_password, verify_password
from app.queries import follows as follows_q
from app.queries import settings as settings_q
from app.queries import users as users_q

_ALLOWED_PRIVACY = {"public", "friends", "private"}


async def settings_defaults(conn: asyncpg.Connection, user_id: int) -> None:
    await settings_q.insert_default_privacy(conn, user_id)


async def change_password(
    conn: asyncpg.Connection,
    user_id: int,
    current_password: str,
    new_password: str,
    confirm_new_password: str,
) -> str:
    current_password = current_password.strip().replace("<", "").replace(">", "")
    new_password = new_password.strip().replace("<", "").replace(">", "")
    confirm_new_password = confirm_new_password.strip().replace("<", "").replace(">", "")

    password_hash = await settings_q.get_password_hash(conn, user_id)
    if password_hash is None or not verify_password(current_password, password_hash):
        return "Incorrect password"

    if new_password != confirm_new_password:
        return "New passwords don't match"

    await settings_q.update_password(conn, user_id, hash_password(new_password))
    return "Password changed"


async def account_type(conn: asyncpg.Connection, user_id: int) -> str | None:
    return await settings_q.get_account_type(conn, user_id)


async def change_account_type(conn: asyncpg.Connection, user_id: int, value: str) -> str | None:
    await settings_q.update_account_type(conn, user_id, value)
    return await settings_q.get_account_type(conn, user_id)


async def block(conn: asyncpg.Connection, blocker_id: int, user_id: int) -> str | None:
    if await settings_q.is_blocked(conn, blocker_id, user_id):
        return None

    await settings_q.create_block(conn, blocker_id, user_id)
    await follows_q.delete_follow_by_pair(conn, follower_id=user_id, followee_id=blocker_id)

    row = await users_q.get_user_by_id(conn, user_id)
    return row["username"] if row else None


async def is_blocked(conn: asyncpg.Connection, blocker_id: int, user_id: int) -> bool:
    return await settings_q.is_blocked(conn, blocker_id, user_id)


async def am_i_blocked(conn: asyncpg.Connection, viewer_id: int, user_id: int) -> bool:
    return await settings_q.is_blocked(conn, user_id, viewer_id)


async def unblock(conn: asyncpg.Connection, blocker_id: int, user_id: int) -> str | None:
    result = await settings_q.delete_block(conn, blocker_id, user_id)
    if result is None:
        return None

    row = await users_q.get_user_by_id(conn, user_id)
    return row["username"] if row else None


async def blocked_users(conn: asyncpg.Connection, user_id: int) -> list[dict]:
    rows = await settings_q.list_blocked_users(conn, user_id)
    return [
        {
            "id": row["id"],
            "username": row["username"],
            "display_name": row["display_name"],
            "blocked_at": row["time"],
        }
        for row in rows
    ]


async def email_privacy(conn: asyncpg.Connection, user_id: int) -> str | None:
    return await settings_q.get_email_privacy(conn, user_id)


async def mobile_privacy(conn: asyncpg.Connection, user_id: int) -> str | None:
    return await settings_q.get_mobile_privacy(conn, user_id)


async def change_email_privacy(conn: asyncpg.Connection, user_id: int, value: str) -> None:
    if value not in _ALLOWED_PRIVACY:
        raise ValueError(f"invalid privacy option: {value!r}")
    await settings_q.update_email_privacy(conn, user_id, value)


async def change_mobile_privacy(conn: asyncpg.Connection, user_id: int, value: str) -> None:
    if value not in _ALLOWED_PRIVACY:
        raise ValueError(f"invalid privacy option: {value!r}")
    await settings_q.update_mobile_privacy(conn, user_id, value)


async def login_details(conn: asyncpg.Connection, user_id: int) -> list[dict]:
    rows = await settings_q.list_login_history(conn, user_id)
    return [
        {
            "time": row["time"],
            "os": row["os"],
            "browser": row["browser"],
            "ip": row["ip"],
            "logout": row["logout_time"] if row["logout_time"] is not None else "By the browser",
        }
        for row in rows
    ]
