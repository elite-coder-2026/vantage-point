"""
Avatar component: business logic sitting on top of app/queries/users.py's
avatar_path column.

This is the piece flagged as an outstanding gap in issues.md: the config
already declared avatar_storage_path/avatar_base_url and the users table
already had an avatar_path column (added for post.php's post-author
pictures), but nothing served that directory over HTTP and no upload/read
path existed. This closes that: an upload endpoint (see
app/routers/users.py), a mount for the storage directory (see
app/main.py), and a URL helper so viewers without an avatar get `None`
(the frontend shows a placeholder) instead of a link to a file that was
never uploaded.
"""

import secrets

from app.config import settings
from app.queries import users as users_q

_AVATAR_EXTS = {"jpg", "jpeg", "png", "gif"}


def avatar_url(avatar_path: str | None) -> str | None:
    if avatar_path is None:
        return None
    return f"{settings.avatar_base_url}/{avatar_path}"


def _store_avatar(content: bytes, original_name: str) -> str:
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if ext not in _AVATAR_EXTS:
        raise ValueError(f"file type .{ext} is not allowed")
    if len(content) > settings.max_avatar_bytes:
        raise ValueError("file is too large")

    settings.avatar_storage_path.mkdir(parents=True, exist_ok=True)
    stored_name = f"{secrets.token_hex(16)}.{ext}"
    (settings.avatar_storage_path / stored_name).write_bytes(content)
    return stored_name


async def upload_avatar(conn, user_id: int, content: bytes, filename: str) -> dict:
    old_path = await users_q.get_user_by_id(conn, user_id)
    stored_name = _store_avatar(content, filename)
    row = await users_q.update_avatar_path(conn, user_id, stored_name)

    if old_path is not None and old_path["avatar_path"] is not None:
        (settings.avatar_storage_path / old_path["avatar_path"]).unlink(missing_ok=True)

    data = dict(row)
    data["avatar_path"] = avatar_url(data["avatar_path"])
    return data
