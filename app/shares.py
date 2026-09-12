"""
Share component: business logic sitting on top of app/queries/shares.py.

Ported from the `share` calls referenced throughout post.php (`getShares`,
`AmIsharedTo`, `AmIsharedBy`). Not provided as a standalone class, so this
is a minimal reconstruction of what post.php actually calls: sharing a post
to another user, undoing that, and the two viewer-relative checks used to
decide which "Unshare" / "Remove share" menu item to show.
"""

import asyncpg

from app import notify as notify_svc
from app.queries import shares as shares_q


async def share_post(conn: asyncpg.Connection, post_id: int, share_by: int, share_to: int) -> dict:
    row = await shares_q.create_share(conn, post_id, share_by, share_to)
    await notify_svc.action_notify(conn, by=share_by, to=share_to, post_id=post_id, type_="share")
    return dict(row)


async def unshare(conn: asyncpg.Connection, share_id: int, share_by: int) -> bool:
    return await shares_q.delete_share(conn, share_id, share_by) is not None


async def am_i_shared_by(conn: asyncpg.Connection, post_id: int, user_id: int) -> bool:
    return await shares_q.is_shared_by(conn, post_id, user_id)


async def am_i_shared_to(conn: asyncpg.Connection, post_id: int, user_id: int) -> bool:
    return await shares_q.is_shared_to(conn, post_id, user_id)


async def get_shares(conn: asyncpg.Connection, post_id: int) -> int:
    return await shares_q.count_shares(conn, post_id)
