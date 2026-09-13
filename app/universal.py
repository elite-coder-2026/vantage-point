import re

import asyncpg

from app.queries import follows as follows_q
from app.queries import universal as queries

_URL_RE = re.compile(
    r"[-a-zA-Z0-9@:%_+.~#?&//=]{2,256}\.[a-z]{2,4}\b(?:/[-a-zA-Z0-9@:%_+.~#'\"?&//=]*)?",
    re.IGNORECASE | re.DOTALL,
)


def is_logged_in(session_user_id: int | None) -> bool:
    return session_user_id is not None


async def get_username_from_session(conn: asyncpg.Connection, session_user_id: int | None) -> str | None:
    if session_user_id is None:
        return None
    row = await queries.get_username_by_id(conn, session_user_id)
    return row["username"] if row else None


def check_get(get) -> bool:
    return get is not None


async def valid_get(conn: asyncpg.Connection, username: str) -> bool:
    return await queries.get_id_by_username(conn, username) is not None


async def get_id_from_get(conn: asyncpg.Connection, username: str) -> int | None:
    row = await queries.get_id_by_username(conn, username)
    return row["id"] if row else None


async def gets_details(conn: asyncpg.Connection, get_id: int, what: str):
    row = await queries.get_user_detail(conn, get_id, what)
    return row[what] if row else None


def me_or_not(get: int, session_user_id: int | None) -> bool:
    if not is_logged_in(session_user_id):
        return False
    return session_user_id == get


async def e_verified(conn: asyncpg.Connection, user_id: int) -> bool:
    # no email_activated column in this schema yet; will raise until added
    email_activated = await gets_details(conn, user_id, "email_activated")
    return email_activated != "no"


async def is_private(conn: asyncpg.Connection, get: int, session_user_id: int | None) -> bool:
    if me_or_not(get, session_user_id):
        return False
    if session_user_id is not None and await follows_q.is_accepted_follower(conn, session_user_id, get):
        return False
    row = await queries.get_user_detail(conn, get, "is_private")
    return bool(row["is_private"]) if row else False


def name_shortener(name: str, limit: int) -> str:
    if len(name) >= limit:
        return name[: int(limit) - 2] + ".."
    return name


def to_abs_url(text: str) -> str:
    return _URL_RE.sub(
        lambda m: f'<a class="hashtag" href="{m.group(0)}" target="_blank">{m.group(0)}</a>',
        text,
    )


async def is_online(conn: asyncpg.Connection, user_id: int, session_user_id: int | None) -> bool | None:
    # no login/logout table in this schema yet
    return None


def url_checker(url: str) -> str:
    if url.startswith("/"):
        return f"http://localhost{url}"
    return url
