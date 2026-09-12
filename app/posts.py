"""
Post component: business logic sitting on top of app/queries/posts.py and
the sibling engagement query modules (likes, comments, shares, taggings,
mentions).

Ported from a PHP `post` class that echoed jQuery-era HTML strings for every
feed variant (getHomePost, getUserPost, getTaggedPost, getSharedPost,
getBookmarksPost, getPhotosPost, getVideosPost, getAudiosPost, viewPost) and
pulled the viewer id from $_SESSION. This version returns structured data
(rendering belongs in Jinja2 templates, matching the rest of app/templates/)
and takes the viewer id as an explicit argument, matching this codebase's
dependency style (see app/notify.py, app/settings.py).

Per-type caption columns (text_post.text, image_post.about, video_post.about,
...) are consolidated into a single posts.body column, since the rest of
this codebase (feed/hashtag routes, PostCreate) already treats `body` as
the one caption field for every post.

Not ported:
- `getLink()`'s server-side link-preview scraping (fetches an arbitrary
  caller-supplied URL and returns its <title>/images). No HTTP client is a
  project dependency, and fetching arbitrary URLs from the server is an
  SSRF vector. Link posts here take a client-supplied url/title/image_url
  instead of the server fetching the page itself.
- The `Avatar` class (upload/crop/serve a profile picture) isn't part of
  post.php and wasn't provided; only a plain `users.avatar_path` column
  exists so post authors can be rendered with a picture once that
  component is ported.
- File names are generated with `secrets.token_hex` instead of the
  original's `time()`-based name, which collides under concurrent uploads
  and is guessable.
"""

import re
import secrets
from datetime import datetime

import asyncpg

from app import notify as notify_svc
from app.config import settings
from app.queries import hashtags as hashtags_q
from app.queries import mentions as mentions_q
from app.queries import posts as posts_q
from app.queries import taggings as taggings_q
from app.queries import users as users_q

_HASHTAG_RE = re.compile(r"#(\w+)")
_MENTION_RE = re.compile(r"@(\w+)")

_IMAGE_EXTS = {"jpg", "jpeg", "png", "gif"}
_VIDEO_EXTS = {"mp4", "ogg"}
_AUDIO_EXTS = {"mp3"}
_DOCUMENT_EXTS = {"js", "css", "html", "txt", "cpp", "py", "ini", "zip", "pdf"}


def extract_hashtags(body: str) -> list[str]:
    seen: dict[str, None] = {}
    for tag in _HASHTAG_RE.findall(body):
        seen.setdefault(tag.lower(), None)
    return list(seen)


def extract_mention_usernames(body: str) -> list[str]:
    seen: dict[str, None] = {}
    for name in _MENTION_RE.findall(body):
        seen.setdefault(name, None)
    return list(seen)


def _store_file(content: bytes, original_name: str, allowed_exts: set[str], max_bytes: int) -> str:
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
    if ext not in allowed_exts:
        raise ValueError(f"file type .{ext} is not allowed")
    if len(content) > max_bytes:
        raise ValueError("file is too large")

    settings.media_storage_path.mkdir(parents=True, exist_ok=True)
    stored_name = f"{secrets.token_hex(16)}.{ext}"
    (settings.media_storage_path / stored_name).write_bytes(content)
    return stored_name


def _media_url(stored_name: str | None) -> str | None:
    if stored_name is None:
        return None
    return f"{settings.media_base_url}/{stored_name}"


async def _apply_hashtags_and_mentions(conn: asyncpg.Connection, post_id: int, body: str) -> None:
    hashtags = extract_hashtags(body)
    if hashtags:
        await hashtags_q.attach_hashtags(conn, post_id, hashtags)

    mention_names = extract_mention_usernames(body)
    if mention_names:
        rows = await users_q.get_users_by_usernames(conn, mention_names)
        if rows:
            await mentions_q.create_mentions(conn, post_id, [r["id"] for r in rows])


async def _apply_taggings(
    conn: asyncpg.Connection, post_id: int, author_id: int, tag_usernames: list[str]
) -> None:
    if not tag_usernames:
        return
    rows = await users_q.get_users_by_usernames(conn, tag_usernames)
    if not rows:
        return
    tagged_ids = [r["id"] for r in rows]
    await taggings_q.tag_users(conn, post_id, tagged_ids)
    for user_id in tagged_ids:
        await notify_svc.action_notify(conn, by=author_id, to=user_id, post_id=post_id, type_="tag")


async def create_text_post(
    conn: asyncpg.Connection, author_id: int, body: str, font_size: int | None = None,
    address: str | None = None, group_id: int | None = None, tag_usernames: list[str] | None = None,
) -> int:
    post_id = await posts_q.create_text_post(conn, author_id, body, font_size, address, group_id)
    await _apply_hashtags_and_mentions(conn, post_id, body)
    await _apply_taggings(conn, post_id, author_id, tag_usernames or [])
    return post_id


async def create_image_post(
    conn: asyncpg.Connection, author_id: int, body: str, file_content: bytes, file_name: str,
    image_filter: str | None = None, font_size: int | None = None, address: str | None = None,
    group_id: int | None = None, tag_usernames: list[str] | None = None,
) -> int:
    stored_name = _store_file(file_content, file_name, _IMAGE_EXTS, settings.max_image_bytes)
    post_id = await posts_q.create_image_post(
        conn, author_id, body, font_size, address, group_id, stored_name, image_filter
    )
    await _apply_hashtags_and_mentions(conn, post_id, body)
    await _apply_taggings(conn, post_id, author_id, tag_usernames or [])
    return post_id


async def create_video_post(
    conn: asyncpg.Connection, author_id: int, body: str, file_content: bytes, file_name: str,
    font_size: int | None = None, address: str | None = None, group_id: int | None = None,
    tag_usernames: list[str] | None = None,
) -> int:
    stored_name = _store_file(file_content, file_name, _VIDEO_EXTS, settings.max_video_bytes)
    post_id = await posts_q.create_video_post(conn, author_id, body, font_size, address, group_id, stored_name)
    await _apply_hashtags_and_mentions(conn, post_id, body)
    await _apply_taggings(conn, post_id, author_id, tag_usernames or [])
    return post_id


async def create_audio_post(
    conn: asyncpg.Connection, author_id: int, body: str, file_content: bytes, file_name: str,
    font_size: int | None = None, address: str | None = None, tag_usernames: list[str] | None = None,
) -> int:
    stored_name = _store_file(file_content, file_name, _AUDIO_EXTS, settings.max_audio_bytes)
    post_id = await posts_q.create_audio_post(conn, author_id, body, font_size, address, stored_name)
    await _apply_hashtags_and_mentions(conn, post_id, body)
    await _apply_taggings(conn, post_id, author_id, tag_usernames or [])
    return post_id


async def create_document_post(
    conn: asyncpg.Connection, author_id: int, body: str, file_content: bytes, file_name: str,
    font_size: int | None = None, address: str | None = None, group_id: int | None = None,
    tag_usernames: list[str] | None = None,
) -> int:
    stored_name = _store_file(file_content, file_name, _DOCUMENT_EXTS, settings.max_document_bytes)
    post_id = await posts_q.create_document_post(
        conn, author_id, body, font_size, address, group_id, stored_name
    )
    await _apply_hashtags_and_mentions(conn, post_id, body)
    await _apply_taggings(conn, post_id, author_id, tag_usernames or [])
    return post_id


async def create_location_post(
    conn: asyncpg.Connection, author_id: int, body: str, image_url: str, font_size: int | None = None,
    address: str | None = None, group_id: int | None = None, tag_usernames: list[str] | None = None,
) -> int:
    post_id = await posts_q.create_location_post(
        conn, author_id, body, font_size, address, group_id, image_url
    )
    await _apply_hashtags_and_mentions(conn, post_id, body)
    await _apply_taggings(conn, post_id, author_id, tag_usernames or [])
    return post_id


async def create_link_post(
    conn: asyncpg.Connection, author_id: int, body: str, url: str, title: str | None = None,
    image_url: str | None = None, font_size: int | None = None, address: str | None = None,
    group_id: int | None = None, tag_usernames: list[str] | None = None,
) -> int:
    post_id = await posts_q.create_link_post(
        conn, author_id, body, font_size, address, group_id, url, title, image_url
    )
    await _apply_hashtags_and_mentions(conn, post_id, body)
    await _apply_taggings(conn, post_id, author_id, tag_usernames or [])
    return post_id


def _row_to_dict(row: asyncpg.Record) -> dict:
    data = dict(row)
    data["image_path"] = _media_url(data.get("image_path"))
    data["video_path"] = _media_url(data.get("video_path"))
    data["audio_path"] = _media_url(data.get("audio_path"))
    data["document_path"] = _media_url(data.get("document_path"))
    return data


async def get_post(conn: asyncpg.Connection, viewer_id: int | None, post_id: int) -> dict | None:
    row = await posts_q.get_post(conn, viewer_id, post_id)
    return _row_to_dict(row) if row else None


async def delete_post(conn: asyncpg.Connection, post_id: int, author_id: int) -> bool:
    post_type = await posts_q.get_post_type(conn, post_id)
    if post_type is None:
        return False

    attachment_path = await posts_q.get_post_attachment_path(conn, post_id, post_type)
    deleted = await posts_q.delete_post(conn, post_id, author_id)
    if deleted is None:
        return False

    if attachment_path is not None:
        file_path = settings.media_storage_path / attachment_path
        file_path.unlink(missing_ok=True)

    return True


async def edit_post(conn: asyncpg.Connection, post_id: int, author_id: int, body: str) -> bool:
    post_type = await posts_q.get_post_type(conn, post_id)
    if post_type is None:
        return False

    if post_type == "text" and body.strip() == "":
        return await delete_post(conn, post_id, author_id)

    updated = await posts_q.update_post_body(conn, post_id, author_id, body)
    if updated is None:
        return False

    await hashtags_q.clear_hashtags(conn, post_id)
    await mentions_q.clear_mentions(conn, post_id)
    await _apply_hashtags_and_mentions(conn, post_id, body)
    return True


async def untag_self(conn: asyncpg.Connection, post_id: int, user_id: int) -> None:
    await taggings_q.untag_user(conn, post_id, user_id)


async def list_feed(
    conn: asyncpg.Connection, viewer_id: int, limit: int, before: datetime | None
) -> list[dict]:
    rows = await posts_q.list_feed_posts(conn, viewer_id, limit, before)
    return [_row_to_dict(r) for r in rows]


async def list_user_posts(
    conn: asyncpg.Connection, viewer_id: int | None, author_id: int, limit: int, before: datetime | None
) -> list[dict]:
    rows = await posts_q.list_user_posts(conn, viewer_id, author_id, limit, before)
    return [_row_to_dict(r) for r in rows]


async def list_tagged(
    conn: asyncpg.Connection, viewer_id: int | None, tagged_user_id: int, limit: int, before_id: int | None
) -> list[dict]:
    rows = await posts_q.list_tagged_posts(conn, viewer_id, tagged_user_id, limit, before_id)
    return [_row_to_dict(r) for r in rows]


async def list_shared(
    conn: asyncpg.Connection, viewer_id: int | None, share_to_id: int, limit: int, before_id: int | None
) -> list[dict]:
    rows = await posts_q.list_shared_posts(conn, viewer_id, share_to_id, limit, before_id)
    return [_row_to_dict(r) for r in rows]


async def list_bookmarked(
    conn: asyncpg.Connection, viewer_id: int, limit: int, before_id: int | None
) -> list[dict]:
    rows = await posts_q.list_bookmarked_posts(conn, viewer_id, limit, before_id)
    return [_row_to_dict(r) for r in rows]


async def list_photos(conn: asyncpg.Connection, author_id: int, limit: int) -> list[dict]:
    rows = await posts_q.list_photos(conn, author_id, limit)
    return [{**dict(r), "path": _media_url(r["path"])} for r in rows]


async def list_videos(conn: asyncpg.Connection, author_id: int, limit: int) -> list[dict]:
    rows = await posts_q.list_videos(conn, author_id, limit)
    return [{**dict(r), "path": _media_url(r["path"])} for r in rows]


async def list_audios(conn: asyncpg.Connection, author_id: int, limit: int) -> list[dict]:
    rows = await posts_q.list_audios(conn, author_id, limit)
    return [{**dict(r), "path": _media_url(r["path"])} for r in rows]


async def post_count(conn: asyncpg.Connection, author_id: int) -> int:
    return await posts_q.post_count(conn, author_id)
