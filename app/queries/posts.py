from datetime import datetime

import asyncpg

POST_SELECT_SQL = """
    SELECT
        p.id, p.author_id, p.group_id, p.type, p.body, p.font_size, p.address, p.created_at,
        img.path AS image_path, img.filter AS image_filter,
        vid.path AS video_path,
        aud.path AS audio_path,
        doc.path AS document_path,
        loc.image_url AS location_image_url,
        lnk.url AS link_url, lnk.title AS link_title, lnk.image_url AS link_image_url,
        (SELECT COUNT(*) FROM post_likes WHERE post_id = p.id) AS like_count,
        (SELECT COUNT(*) FROM post_comments WHERE post_id = p.id AND deleted_at IS NULL) AS comment_count,
        (SELECT COUNT(*) FROM post_shares WHERE post_id = p.id) AS share_count,
        (SELECT COUNT(*) FROM post_taggings WHERE post_id = p.id) AS tag_count,
        EXISTS(SELECT 1 FROM post_likes WHERE post_id = p.id AND user_id = $1) AS liked_by_viewer,
        EXISTS(SELECT 1 FROM bookmarks WHERE post_id = p.id AND user_id = $1) AS bookmarked_by_viewer
    FROM posts p
    LEFT JOIN post_images img ON img.post_id = p.id
    LEFT JOIN post_videos vid ON vid.post_id = p.id
    LEFT JOIN post_audios aud ON aud.post_id = p.id
    LEFT JOIN post_documents doc ON doc.post_id = p.id
    LEFT JOIN post_locations loc ON loc.post_id = p.id
    LEFT JOIN post_links lnk ON lnk.post_id = p.id
"""


async def create_text_post(
    conn: asyncpg.Connection, author_id: int, body: str, font_size: int | None,
    address: str | None, group_id: int | None,
) -> int:
    return await conn.fetchval(
        """
        INSERT INTO posts (author_id, group_id, type, body, font_size, address)
        VALUES ($1, $2, 'text', $3, $4, $5)
        RETURNING id
        """,
        author_id, group_id, body, font_size, address,
    )


async def create_image_post(
    conn: asyncpg.Connection, author_id: int, body: str, font_size: int | None,
    address: str | None, group_id: int | None, image_path: str, image_filter: str | None,
) -> int:
    async with conn.transaction():
        post_id = await conn.fetchval(
            """
            INSERT INTO posts (author_id, group_id, type, body, font_size, address)
            VALUES ($1, $2, 'image', $3, $4, $5)
            RETURNING id
            """,
            author_id, group_id, body, font_size, address,
        )
        await conn.execute(
            "INSERT INTO post_images (post_id, path, filter) VALUES ($1, $2, $3)",
            post_id, image_path, image_filter,
        )
    return post_id


async def create_video_post(
    conn: asyncpg.Connection, author_id: int, body: str, font_size: int | None,
    address: str | None, group_id: int | None, video_path: str,
) -> int:
    async with conn.transaction():
        post_id = await conn.fetchval(
            """
            INSERT INTO posts (author_id, group_id, type, body, font_size, address)
            VALUES ($1, $2, 'video', $3, $4, $5)
            RETURNING id
            """,
            author_id, group_id, body, font_size, address,
        )
        await conn.execute(
            "INSERT INTO post_videos (post_id, path) VALUES ($1, $2)", post_id, video_path,
        )
    return post_id


async def create_audio_post(
    conn: asyncpg.Connection, author_id: int, body: str, font_size: int | None,
    address: str | None, audio_path: str,
) -> int:
    async with conn.transaction():
        post_id = await conn.fetchval(
            """
            INSERT INTO posts (author_id, type, body, font_size, address)
            VALUES ($1, 'audio', $2, $3, $4)
            RETURNING id
            """,
            author_id, body, font_size, address,
        )
        await conn.execute(
            "INSERT INTO post_audios (post_id, path) VALUES ($1, $2)", post_id, audio_path,
        )
    return post_id


async def create_document_post(
    conn: asyncpg.Connection, author_id: int, body: str, font_size: int | None,
    address: str | None, group_id: int | None, document_path: str,
) -> int:
    async with conn.transaction():
        post_id = await conn.fetchval(
            """
            INSERT INTO posts (author_id, group_id, type, body, font_size, address)
            VALUES ($1, $2, 'document', $3, $4, $5)
            RETURNING id
            """,
            author_id, group_id, body, font_size, address,
        )
        await conn.execute(
            "INSERT INTO post_documents (post_id, path) VALUES ($1, $2)", post_id, document_path,
        )
    return post_id


async def create_location_post(
    conn: asyncpg.Connection, author_id: int, body: str, font_size: int | None,
    address: str | None, group_id: int | None, image_url: str,
) -> int:
    async with conn.transaction():
        post_id = await conn.fetchval(
            """
            INSERT INTO posts (author_id, group_id, type, body, font_size, address)
            VALUES ($1, $2, 'location', $3, $4, $5)
            RETURNING id
            """,
            author_id, group_id, body, font_size, address,
        )
        await conn.execute(
            "INSERT INTO post_locations (post_id, image_url) VALUES ($1, $2)", post_id, image_url,
        )
    return post_id


async def create_link_post(
    conn: asyncpg.Connection, author_id: int, body: str, font_size: int | None,
    address: str | None, group_id: int | None, url: str, title: str | None, image_url: str | None,
) -> int:
    async with conn.transaction():
        post_id = await conn.fetchval(
            """
            INSERT INTO posts (author_id, group_id, type, body, font_size, address)
            VALUES ($1, $2, 'link', $3, $4, $5)
            RETURNING id
            """,
            author_id, group_id, body, font_size, address,
        )
        await conn.execute(
            "INSERT INTO post_links (post_id, url, title, image_url) VALUES ($1, $2, $3, $4)",
            post_id, url, title, image_url,
        )
    return post_id


async def get_post(conn: asyncpg.Connection, viewer_id: int | None, post_id: int) -> asyncpg.Record | None:
    return await conn.fetchrow(POST_SELECT_SQL + " WHERE p.id = $2", viewer_id, post_id)


async def get_post_author(conn: asyncpg.Connection, post_id: int) -> int | None:
    return await conn.fetchval("SELECT author_id FROM posts WHERE id = $1", post_id)


async def get_post_type(conn: asyncpg.Connection, post_id: int) -> str | None:
    return await conn.fetchval("SELECT type FROM posts WHERE id = $1", post_id)


async def get_post_attachment_path(conn: asyncpg.Connection, post_id: int, post_type: str) -> str | None:
    table = {
        "image": "post_images",
        "video": "post_videos",
        "audio": "post_audios",
        "document": "post_documents",
    }.get(post_type)
    if table is None:
        return None
    return await conn.fetchval(f"SELECT path FROM {table} WHERE post_id = $1", post_id)


async def delete_post(conn: asyncpg.Connection, post_id: int, author_id: int) -> str | None:
    return await conn.fetchval(
        "DELETE FROM posts WHERE id = $1 AND author_id = $2 RETURNING 'ok'", post_id, author_id,
    )


async def update_post_body(conn: asyncpg.Connection, post_id: int, author_id: int, body: str) -> str | None:
    return await conn.fetchval(
        "UPDATE posts SET body = $3, updated_at = now() WHERE id = $1 AND author_id = $2 RETURNING 'ok'",
        post_id, author_id, body,
    )


async def post_count(conn: asyncpg.Connection, author_id: int) -> int:
    return await conn.fetchval(
        "SELECT COUNT(*) FROM posts WHERE author_id = $1 AND group_id IS NULL", author_id,
    )


async def list_feed_posts(
    conn: asyncpg.Connection, viewer_id: int, limit: int, before: datetime | None,
) -> list[asyncpg.Record]:
    return await conn.fetch(
        POST_SELECT_SQL + """
        WHERE p.group_id IS NULL
          AND (p.author_id = $1 OR p.author_id IN (
              SELECT followee_id FROM follows WHERE follower_id = $1 AND status = 'accepted'
          ))
          AND ($3::timestamptz IS NULL OR p.created_at < $3)
        ORDER BY p.created_at DESC
        LIMIT $2
        """,
        viewer_id, limit, before,
    )


async def list_user_posts(
    conn: asyncpg.Connection, viewer_id: int | None, author_id: int, limit: int, before: datetime | None,
) -> list[asyncpg.Record]:
    return await conn.fetch(
        POST_SELECT_SQL + """
        WHERE p.author_id = $2 AND p.group_id IS NULL
          AND ($4::timestamptz IS NULL OR p.created_at < $4)
        ORDER BY p.created_at DESC
        LIMIT $3
        """,
        viewer_id, author_id, limit, before,
    )


async def list_tagged_posts(
    conn: asyncpg.Connection, viewer_id: int | None, tagged_user_id: int, limit: int, before_id: int | None,
) -> list[asyncpg.Record]:
    return await conn.fetch(
        POST_SELECT_SQL + """
        JOIN post_taggings pt ON pt.post_id = p.id
        WHERE pt.tagged_user_id = $2
          AND ($4::bigint IS NULL OR pt.id < $4)
        ORDER BY pt.id DESC
        LIMIT $3
        """,
        viewer_id, tagged_user_id, limit, before_id,
    )


async def list_shared_posts(
    conn: asyncpg.Connection, viewer_id: int | None, share_to_id: int, limit: int, before_id: int | None,
) -> list[asyncpg.Record]:
    return await conn.fetch(
        POST_SELECT_SQL + """
        JOIN post_shares ps ON ps.post_id = p.id
        WHERE ps.share_to = $2
          AND ($4::bigint IS NULL OR ps.id < $4)
        ORDER BY ps.id DESC
        LIMIT $3
        """,
        viewer_id, share_to_id, limit, before_id,
    )


async def list_bookmarked_posts(
    conn: asyncpg.Connection, viewer_id: int, limit: int, before_id: int | None,
) -> list[asyncpg.Record]:
    return await conn.fetch(
        POST_SELECT_SQL + """
        JOIN bookmarks bm ON bm.post_id = p.id
        WHERE bm.user_id = $1
          AND ($3::bigint IS NULL OR bm.bkmrk_id < $3)
        ORDER BY bm.bkmrk_id DESC
        LIMIT $2
        """,
        viewer_id, limit, before_id,
    )


async def list_photos(conn: asyncpg.Connection, author_id: int, limit: int) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT p.id, p.created_at, img.path, img.filter,
            (SELECT COUNT(*) FROM post_likes WHERE post_id = p.id) AS like_count,
            (SELECT COUNT(*) FROM post_comments WHERE post_id = p.id AND deleted_at IS NULL) AS comment_count
        FROM posts p JOIN post_images img ON img.post_id = p.id
        WHERE p.author_id = $1 AND p.group_id IS NULL
        ORDER BY p.created_at DESC
        LIMIT $2
        """,
        author_id, limit,
    )


async def list_videos(conn: asyncpg.Connection, author_id: int, limit: int) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT p.id, p.created_at, vid.path
        FROM posts p JOIN post_videos vid ON vid.post_id = p.id
        WHERE p.author_id = $1 AND p.group_id IS NULL
        ORDER BY p.created_at DESC
        LIMIT $2
        """,
        author_id, limit,
    )


async def list_audios(conn: asyncpg.Connection, author_id: int, limit: int) -> list[asyncpg.Record]:
    return await conn.fetch(
        """
        SELECT p.id, p.created_at, aud.path
        FROM posts p JOIN post_audios aud ON aud.post_id = p.id
        WHERE p.author_id = $1 AND p.group_id IS NULL
        ORDER BY p.created_at DESC
        LIMIT $2
        """,
        author_id, limit,
    )
