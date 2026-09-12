import asyncpg
from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app import avatar as avatar_svc
from app import comments as comments_svc
from app import forgot_password as forgot_password_svc
from app import likes as likes_svc
from app import notify as notify_svc
from app import posts as posts_svc
from app import settings as settings_svc
from app.auth import (
    SESSION_COOKIE_NAME,
    generate_session_token,
    get_current_user_id_optional,
    hash_password,
    session_expiry,
    verify_password,
)
from app.db import get_conn
from app.queries import bkmrk as bkmrk_q
from app.queries import follows as follows_q
from app.queries import notify as notify_q
from app.queries import sessions as sessions_q
from app.queries import users as users_q
from app.timeago import normal_time, time_ago

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="app/templates")
templates.env.filters["time_ago"] = time_ago
templates.env.filters["normal_time"] = normal_time


async def _current_user(conn, current_user_id):
    if current_user_id is None:
        return None
    user = await users_q.get_user_by_id(conn, current_user_id)
    if user is None:
        return None
    unread = await notify_q.count_unread(conn, current_user_id)
    return {**user, "has_unread_notifications": unread > 0}


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"current_user": None})


@router.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    conn: asyncpg.Connection = Depends(get_conn),
):
    row = await users_q.get_user_by_username_with_auth(conn, username)
    if row is None or not verify_password(password, row["password_hash"]):
        return templates.TemplateResponse(
            request, "login.html", {"current_user": None, "error": "Invalid credentials"},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    token, token_hash = generate_session_token()
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    await sessions_q.create_session(conn, row["id"], token_hash, session_expiry(), user_agent, ip_address)

    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        SESSION_COOKIE_NAME, token, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 14,
    )
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request, "register.html", {"current_user": None})


@router.post("/register")
async def register_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    display_name: str = Form(...),
    password: str = Form(...),
    conn: asyncpg.Connection = Depends(get_conn),
):
    existing = await users_q.get_user_by_username_with_auth(conn, username)
    if existing is not None:
        return templates.TemplateResponse(
            request, "register.html", {"current_user": None, "error": "Username already taken"},
            status_code=status.HTTP_409_CONFLICT,
        )

    row = await users_q.create_user(conn, username, email, hash_password(password), display_name)

    token, token_hash = generate_session_token()
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    await sessions_q.create_session(conn, row["id"], token_hash, session_expiry(), user_agent, ip_address)

    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        SESSION_COOKIE_NAME, token, httponly=True, samesite="lax", max_age=60 * 60 * 24 * 14,
    )
    return response


@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse(request, "forgot-password.html", {"current_user": None})


@router.post("/forgot-password")
async def forgot_password_submit(
    request: Request,
    email: str = Form(...),
    conn: asyncpg.Connection = Depends(get_conn),
):
    await forgot_password_svc.request_reset(conn, email)
    return templates.TemplateResponse(
        request, "forgot-password.html", {"current_user": None, "sent": True}
    )


@router.get("/reset-password/{token}", response_class=HTMLResponse)
async def reset_password_page(request: Request, token: str):
    return templates.TemplateResponse(
        request, "reset-password.html", {"current_user": None, "token": token}
    )


@router.post("/reset-password/{token}")
async def reset_password_submit(
    request: Request,
    token: str,
    new_password: str = Form(...),
    confirm_new_password: str = Form(...),
    conn: asyncpg.Connection = Depends(get_conn),
):
    message = await forgot_password_svc.reset_password(conn, token, new_password, confirm_new_password)
    if message != "Password reset":
        return templates.TemplateResponse(
            request,
            "reset-password.html",
            {"current_user": None, "token": token, "error": message},
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/logout")
async def logout_submit(
    request: Request,
    conn: asyncpg.Connection = Depends(get_conn),
):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        import hashlib

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        await sessions_q.revoke_session(conn, token_hash)

    response = RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(SESSION_COOKIE_NAME)
    return response


@router.get("/", response_class=HTMLResponse)
async def feed_page(
    request: Request,
    current_user_id: int | None = Depends(get_current_user_id_optional),
    conn: asyncpg.Connection = Depends(get_conn),
):
    if current_user_id is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    current_user = await _current_user(conn, current_user_id)
    rows = await posts_svc.list_feed(conn, current_user_id, 20, None)

    posts = []
    author_cache: dict[int, str] = {}
    for r in rows:
        author_id = r["author_id"]
        if author_id not in author_cache:
            author = await users_q.get_user_by_id(conn, author_id)
            author_cache[author_id] = author["username"] if author else "unknown"
        posts.append({**dict(r), "author_username": author_cache[author_id]})

    return templates.TemplateResponse(
        request, "feed.html", {"current_user": current_user, "posts": posts}
    )


@router.post("/posts/new")
async def create_post_submit(
    request: Request,
    body: str = Form(...),
    current_user_id: int | None = Depends(get_current_user_id_optional),
    conn: asyncpg.Connection = Depends(get_conn),
):
    if current_user_id is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    await posts_svc.create_text_post(conn, current_user_id, body)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/u/{username}", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    username: str,
    current_user_id: int | None = Depends(get_current_user_id_optional),
    conn: asyncpg.Connection = Depends(get_conn),
):
    profile_user = await users_q.get_user_by_username_with_auth(conn, username)
    if profile_user is None:
        return templates.TemplateResponse(
            request, "base.html", {"current_user": None, "error": "User not found"},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    current_user = await _current_user(conn, current_user_id)

    can_view = True
    posts = []
    if profile_user["is_private"] and profile_user["id"] != current_user_id:
        can_view = (
            current_user_id is not None
            and await follows_q.is_accepted_follower(conn, current_user_id, profile_user["id"])
        )

    if can_view:
        posts = await posts_svc.list_user_posts(conn, current_user_id, profile_user["id"], 20, None)

    post_count = await posts_svc.post_count(conn, profile_user["id"])
    follower_count = await follows_q.count_followers(conn, profile_user["id"])
    following_count = await follows_q.count_following(conn, profile_user["id"])

    return templates.TemplateResponse(
        request,
        "profile.html",
        {
            "current_user": current_user,
            "profile_user": profile_user,
            "can_view": can_view,
            "posts": posts,
            "post_count": post_count,
            "follower_count": follower_count,
            "following_count": following_count,
        },
    )


async def _settings_context(conn, current_user, **extra):
    user_id = current_user["id"]
    return {
        "current_user": current_user,
        "account_type": await settings_svc.account_type(conn, user_id),
        "email_privacy": await settings_svc.email_privacy(conn, user_id),
        "mobile_privacy": await settings_svc.mobile_privacy(conn, user_id),
        "blocked": await settings_svc.blocked_users(conn, user_id),
        "login_history": await settings_svc.login_details(conn, user_id),
        **extra,
    }


@router.get("/settings", response_class=HTMLResponse)
async def settings_page(
    request: Request,
    current_user_id: int | None = Depends(get_current_user_id_optional),
    conn: asyncpg.Connection = Depends(get_conn),
):
    if current_user_id is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    current_user = await _current_user(conn, current_user_id)
    return templates.TemplateResponse(
        request, "settings.html", await _settings_context(conn, current_user)
    )


@router.post("/settings/update-password")
async def settings_update_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_new_password: str = Form(...),
    current_user_id: int | None = Depends(get_current_user_id_optional),
    conn: asyncpg.Connection = Depends(get_conn),
):
    if current_user_id is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    current_user = await _current_user(conn, current_user_id)
    message = await settings_svc.change_password(
        conn, current_user_id, current_password, new_password, confirm_new_password
    )
    return templates.TemplateResponse(
        request,
        "settings.html",
        await _settings_context(conn, current_user, password_message=message),
    )


@router.post("/settings/update-account-type")
async def settings_update_account_type(
    request: Request,
    value: str = Form(...),
    current_user_id: int | None = Depends(get_current_user_id_optional),
    conn: asyncpg.Connection = Depends(get_conn),
):
    if current_user_id is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    await settings_svc.change_account_type(conn, current_user_id, value)
    return RedirectResponse("/settings", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/settings/update-email-privacy")
async def settings_update_email_privacy(
    request: Request,
    value: str = Form(...),
    current_user_id: int | None = Depends(get_current_user_id_optional),
    conn: asyncpg.Connection = Depends(get_conn),
):
    if current_user_id is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    await settings_svc.change_email_privacy(conn, current_user_id, value)
    return RedirectResponse("/settings", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/settings/update-mobile-privacy")
async def settings_update_mobile_privacy(
    request: Request,
    value: str = Form(...),
    current_user_id: int | None = Depends(get_current_user_id_optional),
    conn: asyncpg.Connection = Depends(get_conn),
):
    if current_user_id is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    await settings_svc.change_mobile_privacy(conn, current_user_id, value)
    return RedirectResponse("/settings", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/settings/unblock-user/{target_id}")
async def settings_unblock_user(
    request: Request,
    target_id: int,
    current_user_id: int | None = Depends(get_current_user_id_optional),
    conn: asyncpg.Connection = Depends(get_conn),
):
    if current_user_id is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    await settings_svc.unblock(conn, current_user_id, target_id)
    return RedirectResponse("/settings", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/view-post/{post_id}", response_class=HTMLResponse)
async def view_post_page(
    request: Request,
    post_id: int,
    current_user_id: int | None = Depends(get_current_user_id_optional),
    conn: asyncpg.Connection = Depends(get_conn),
):
    post = await posts_svc.get_post(conn, current_user_id, post_id)
    if post is None:
        return templates.TemplateResponse(
            request, "base.html", {"current_user": None, "error": "Post not found"},
            status_code=status.HTTP_404_NOT_FOUND,
        )

    current_user = await _current_user(conn, current_user_id)
    author = await users_q.get_user_by_id(conn, post["author_id"])

    comment_rows = await comments_svc.get_comments(conn, current_user_id, post_id)
    author_cache: dict[int, str] = {}
    comments = []
    for c in comment_rows:
        commenter_id = c["user_id"]
        if commenter_id not in author_cache:
            commenter = await users_q.get_user_by_id(conn, commenter_id)
            author_cache[commenter_id] = commenter["username"] if commenter else "unknown"
        comments.append({**c, "username": author_cache[commenter_id]})

    return templates.TemplateResponse(
        request,
        "post.html",
        {
            "current_user": current_user,
            "post": post,
            "author": author,
            "comments": comments,
        },
    )


def _safe_next(next_: str | None, post_id: int) -> str:
    if next_ and next_.startswith("/") and not next_.startswith("//"):
        return next_
    return f"/view-post/{post_id}"


@router.post("/view-post/{post_id}/comment")
async def view_post_comment_submit(
    request: Request,
    post_id: int,
    body: str = Form(...),
    next: str | None = Form(None),
    current_user_id: int | None = Depends(get_current_user_id_optional),
    conn: asyncpg.Connection = Depends(get_conn),
):
    if current_user_id is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    await comments_svc.create_comment(conn, post_id, current_user_id, body)
    return RedirectResponse(_safe_next(next, post_id), status_code=status.HTTP_303_SEE_OTHER)


@router.post("/view-post/{post_id}/like")
async def view_post_like_submit(
    post_id: int,
    next: str | None = Form(None),
    current_user_id: int | None = Depends(get_current_user_id_optional),
    conn: asyncpg.Connection = Depends(get_conn),
):
    if current_user_id is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    if await likes_svc.liked_or_not(conn, post_id, current_user_id):
        await likes_svc.unlike_post(conn, post_id, current_user_id)
    else:
        await likes_svc.like_post(conn, post_id, current_user_id)
    return RedirectResponse(_safe_next(next, post_id), status_code=status.HTTP_303_SEE_OTHER)


@router.post("/view-post/{post_id}/bookmark")
async def view_post_bookmark_submit(
    post_id: int,
    next: str | None = Form(None),
    current_user_id: int | None = Depends(get_current_user_id_optional),
    conn: asyncpg.Connection = Depends(get_conn),
):
    if current_user_id is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    if await bkmrk_q.is_bookmarked(conn, post_id, current_user_id):
        await bkmrk_q.delete_bookmark(conn, post_id, current_user_id)
    else:
        await bkmrk_q.create_bookmark(conn, post_id, current_user_id)
    return RedirectResponse(_safe_next(next, post_id), status_code=status.HTTP_303_SEE_OTHER)


@router.post("/view-post/{post_id}/delete")
async def view_post_delete_submit(
    post_id: int,
    current_user_id: int | None = Depends(get_current_user_id_optional),
    conn: asyncpg.Connection = Depends(get_conn),
):
    if current_user_id is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    await posts_svc.delete_post(conn, post_id, current_user_id)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@router.get("/notifications", response_class=HTMLResponse)
async def notifications_page(
    request: Request,
    current_user_id: int | None = Depends(get_current_user_id_optional),
    conn: asyncpg.Connection = Depends(get_conn),
):
    if current_user_id is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    current_user = await _current_user(conn, current_user_id)
    notifications = await notify_svc.get_notifications(conn, current_user_id)
    for n in notifications:
        if n["by"]:
            n["by"]["avatar_path"] = avatar_svc.avatar_url(n["by"]["avatar_path"])
        if n["of"]:
            n["of"]["avatar_path"] = avatar_svc.avatar_url(n["of"]["avatar_path"])

    await notify_svc.mark_read(conn, current_user_id)

    return templates.TemplateResponse(
        request, "notifications.html", {"current_user": current_user, "notifications": notifications}
    )


@router.post("/notifications/clear")
async def notifications_clear_submit(
    current_user_id: int | None = Depends(get_current_user_id_optional),
    conn: asyncpg.Connection = Depends(get_conn),
):
    if current_user_id is None:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

    await notify_svc.clear_notifications(conn, current_user_id)
    return RedirectResponse("/notifications", status_code=status.HTTP_303_SEE_OTHER)
