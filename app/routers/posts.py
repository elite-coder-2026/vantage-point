from datetime import datetime

import asyncpg
from fastapi import APIRouter, Depends, Form, HTTPException, Response, UploadFile, status

from app import comments as comments_svc
from app import likes as likes_svc
from app import posts as posts_svc
from app import shares as shares_svc
from app.auth import get_current_user_id, get_current_user_id_optional
from app.db import get_conn
from app.queries import bkmrk as bkmrk_q
from app.queries import groups as groups_q
from app.schemas.comments import CommentCreate, CommentOut
from app.schemas.posts import LinkPostCreate, LocationPostCreate, PostEdit, PostOut, TextPostCreate
from app.schemas.shares import ShareCreate, ShareOut

router = APIRouter(tags=["posts"])


async def _require_group_membership(conn: asyncpg.Connection, group_id: int | None, user_id: int) -> None:
    if group_id is None:
        return
    if not await groups_q.is_member(conn, group_id, user_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Must be a group member to post")


def _split_tags(tags: str | None) -> list[str]:
    if not tags:
        return []
    return [t.strip() for t in tags.split(",") if t.strip()]


@router.post("/posts", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_text_post(
    payload: TextPostCreate,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await _require_group_membership(conn, payload.group_id, current_user_id)
    post_id = await posts_svc.create_text_post(
        conn, current_user_id, payload.body, payload.font_size, payload.address,
        payload.group_id, payload.tags,
    )
    return PostOut(**await posts_svc.get_post(conn, current_user_id, post_id))


@router.post("/posts/link", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_link_post(
    payload: LinkPostCreate,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await _require_group_membership(conn, payload.group_id, current_user_id)
    post_id = await posts_svc.create_link_post(
        conn, current_user_id, payload.body, payload.url, payload.title, payload.image_url,
        payload.font_size, payload.address, payload.group_id, payload.tags,
    )
    return PostOut(**await posts_svc.get_post(conn, current_user_id, post_id))


@router.post("/posts/location", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_location_post(
    payload: LocationPostCreate,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await _require_group_membership(conn, payload.group_id, current_user_id)
    post_id = await posts_svc.create_location_post(
        conn, current_user_id, payload.body, payload.image_url, payload.font_size, payload.address,
        payload.group_id, payload.tags,
    )
    return PostOut(**await posts_svc.get_post(conn, current_user_id, post_id))


@router.post("/posts/image", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_image_post(
    file: UploadFile,
    body: str = Form(""),
    filter: str | None = Form(None),
    group_id: int | None = Form(None),
    font_size: int | None = Form(None),
    address: str | None = Form(None),
    tags: str | None = Form(None),
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await _require_group_membership(conn, group_id, current_user_id)
    content = await file.read()
    try:
        post_id = await posts_svc.create_image_post(
            conn, current_user_id, body, content, file.filename or "", filter, font_size, address,
            group_id, _split_tags(tags),
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return PostOut(**await posts_svc.get_post(conn, current_user_id, post_id))


@router.post("/posts/video", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_video_post(
    file: UploadFile,
    body: str = Form(""),
    group_id: int | None = Form(None),
    font_size: int | None = Form(None),
    address: str | None = Form(None),
    tags: str | None = Form(None),
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await _require_group_membership(conn, group_id, current_user_id)
    content = await file.read()
    try:
        post_id = await posts_svc.create_video_post(
            conn, current_user_id, body, content, file.filename or "", font_size, address,
            group_id, _split_tags(tags),
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return PostOut(**await posts_svc.get_post(conn, current_user_id, post_id))


@router.post("/posts/audio", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_audio_post(
    file: UploadFile,
    body: str = Form(""),
    font_size: int | None = Form(None),
    address: str | None = Form(None),
    tags: str | None = Form(None),
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    content = await file.read()
    try:
        post_id = await posts_svc.create_audio_post(
            conn, current_user_id, body, content, file.filename or "", font_size, address,
            _split_tags(tags),
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return PostOut(**await posts_svc.get_post(conn, current_user_id, post_id))


@router.post("/posts/document", response_model=PostOut, status_code=status.HTTP_201_CREATED)
async def create_document_post(
    file: UploadFile,
    body: str = Form(""),
    group_id: int | None = Form(None),
    font_size: int | None = Form(None),
    address: str | None = Form(None),
    tags: str | None = Form(None),
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await _require_group_membership(conn, group_id, current_user_id)
    content = await file.read()
    try:
        post_id = await posts_svc.create_document_post(
            conn, current_user_id, body, content, file.filename or "", font_size, address,
            group_id, _split_tags(tags),
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    return PostOut(**await posts_svc.get_post(conn, current_user_id, post_id))


@router.get("/posts/{post_id}", response_model=PostOut)
async def get_post(
    post_id: int,
    current_user_id: int | None = Depends(get_current_user_id_optional),
    conn: asyncpg.Connection = Depends(get_conn),
):
    row = await posts_svc.get_post(conn, current_user_id, post_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")
    return PostOut(**row)


@router.patch("/posts/{post_id}", response_model=PostOut)
async def edit_post(
    post_id: int,
    payload: PostEdit,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    edited = await posts_svc.edit_post(conn, post_id, current_user_id, payload.body)
    if not edited:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")

    row = await posts_svc.get_post(conn, current_user_id, post_id)
    if row is None:
        # An emptied text post is deleted rather than left blank (matches the
        # original PHP's editPost, which calls deletePost when text == "").
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    return PostOut(**row)


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: int,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    deleted = await posts_svc.delete_post(conn, post_id, current_user_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Post not found")


@router.delete("/posts/{post_id}/tag", status_code=status.HTTP_204_NO_CONTENT)
async def untag_self(
    post_id: int,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await posts_svc.untag_self(conn, post_id, current_user_id)


@router.get("/feed", response_model=list[PostOut])
async def get_feed(
    limit: int = 20,
    before: datetime | None = None,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    rows = await posts_svc.list_feed(conn, current_user_id, limit, before)
    return [PostOut(**r) for r in rows]


@router.get("/bookmarks", response_model=list[PostOut])
async def get_bookmarks(
    limit: int = 20,
    before_id: int | None = None,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    rows = await posts_svc.list_bookmarked(conn, current_user_id, limit, before_id)
    return [PostOut(**r) for r in rows]


@router.post("/posts/{post_id}/bookmark", status_code=status.HTTP_204_NO_CONTENT)
async def bookmark_post(
    post_id: int,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    if not await bkmrk_q.is_bookmarked(conn, post_id, current_user_id):
        await bkmrk_q.create_bookmark(conn, post_id, current_user_id)


@router.delete("/posts/{post_id}/bookmark", status_code=status.HTTP_204_NO_CONTENT)
async def unbookmark_post(
    post_id: int,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await bkmrk_q.delete_bookmark(conn, post_id, current_user_id)


@router.post("/posts/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def like_post(
    post_id: int,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await likes_svc.like_post(conn, post_id, current_user_id)


@router.delete("/posts/{post_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_post(
    post_id: int,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await likes_svc.unlike_post(conn, post_id, current_user_id)


@router.get("/posts/{post_id}/comments", response_model=list[CommentOut])
async def get_comments(
    post_id: int,
    limit: int = 20,
    before_id: int | None = None,
    current_user_id: int | None = Depends(get_current_user_id_optional),
    conn: asyncpg.Connection = Depends(get_conn),
):
    rows = await comments_svc.get_comments(conn, current_user_id, post_id, limit, before_id)
    return [CommentOut(**r) for r in rows]


@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
async def create_comment(
    post_id: int,
    payload: CommentCreate,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    row = await comments_svc.create_comment(conn, post_id, current_user_id, payload.body)
    return CommentOut(**row, like_count=0, liked_by_viewer=False)


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comment(
    comment_id: int,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    deleted = await comments_svc.delete_comment(conn, comment_id, current_user_id)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")


@router.post("/comments/{comment_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def like_comment(
    comment_id: int,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await likes_svc.like_comment(conn, comment_id, current_user_id)


@router.delete("/comments/{comment_id}/like", status_code=status.HTTP_204_NO_CONTENT)
async def unlike_comment(
    comment_id: int,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await likes_svc.unlike_comment(conn, comment_id, current_user_id)


@router.post("/posts/{post_id}/share", response_model=ShareOut, status_code=status.HTTP_201_CREATED)
async def share_post(
    post_id: int,
    payload: ShareCreate,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    if payload.share_to == current_user_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Cannot share a post with yourself")
    row = await shares_svc.share_post(conn, post_id, current_user_id, payload.share_to)
    return ShareOut(**row)


@router.delete("/shares/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unshare(
    share_id: int,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    unshared = await shares_svc.unshare(conn, share_id, current_user_id)
    if not unshared:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Share not found")


@router.get("/shared-with-me", response_model=list[PostOut])
async def get_shared_with_me(
    limit: int = 20,
    before_id: int | None = None,
    current_user_id: int = Depends(get_current_user_id),
    conn: asyncpg.Connection = Depends(get_conn),
):
    rows = await posts_svc.list_shared(conn, current_user_id, current_user_id, limit, before_id)
    return [PostOut(**r) for r in rows]
