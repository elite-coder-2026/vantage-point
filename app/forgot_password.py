"""
Forgot-password component: business logic sitting on top of
app/queries/password_resets.py.

Ported from a PHP `forgot` class whose `retrieve()` method looked up a user
by email and mailed them a "Retrieve" link built from their raw numeric
user id (`retrieve.php?id={$uid}`) with no secret token at all — anyone
could reset any account by guessing/incrementing that id. This version
replaces that with a random, single-use, expiring token (same shape as
`app.auth.generate_session_token`), stored hashed like session tokens are.

Also dropped from the original: the `$mail->SMTPDebug` toggle, the two
hardcoded `addAttachment()` calls pulling arbitrary files from `/var/tmp`
and `/tmp` (unrelated debug leftovers, not something to ship), and the
`echo "No such user exists"` branch — telling an anonymous caller whether
an email is registered is a user-enumeration leak, so `request_reset`
always reports success and only sends mail when the address matches an
account. Uses stdlib `smtplib` instead of PHPMailer.

The commented-out `login` insert at the end of the original method (an
$_SESSION-based "log the user in from the reset link" shortcut) is not
ported — logging a user in as a side effect of clicking an emailed link,
before they've proven a new password, is itself a hijack vector.
"""

import hashlib
import secrets
import smtplib
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage

import asyncpg

from app.auth import hash_password
from app.config import settings
from app.queries import password_resets as resets_q
from app.queries import settings as settings_q
from app.queries import users as users_q


def _generate_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    return token, token_hash


def _send_reset_email(to_email: str, reset_url: str) -> None:
    message = EmailMessage()
    message["Subject"] = "Reset your Vantage Point password"
    message["From"] = settings.smtp_username
    message["To"] = to_email
    message.set_content(
        "You received this message because a password reset was requested "
        f"for your Vantage Point account.\n\nReset your password: {reset_url}\n\n"
        "If you didn't request this, you can ignore this email."
    )
    message.add_alternative(
        "<p>You received this message because a password reset was requested "
        "for your Vantage Point account.</p>"
        f"<p><a href='{reset_url}' style=\"border: 1px solid #1b9be9; font-weight: 600; "
        "color: #fff; border-radius: 3px; cursor: pointer; outline: none; background: "
        "#1b9be9; padding: 4px 15px; display: inline-block; text-decoration: none;\">"
        "Reset password</a></p>"
        "<p>If you didn't request this, you can ignore this email.</p>",
        subtype="html",
    )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(message)


async def request_reset(conn: asyncpg.Connection, email: str) -> None:
    email = email.strip().replace("<", "").replace(">", "")

    user = await users_q.get_user_by_email(conn, email)
    if user is None:
        return

    token, token_hash = _generate_token()
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=settings.password_reset_ttl_seconds)
    await resets_q.create_reset_token(conn, user["id"], token_hash, expires_at)

    reset_url = f"{settings.site_url}/reset-password/{token}"
    _send_reset_email(user["email"], reset_url)


async def reset_password(
    conn: asyncpg.Connection, token: str, new_password: str, confirm_new_password: str
) -> str:
    new_password = new_password.strip().replace("<", "").replace(">", "")
    confirm_new_password = confirm_new_password.strip().replace("<", "").replace(">", "")

    token_hash = hashlib.sha256(token.encode()).hexdigest()
    reset = await resets_q.get_valid_reset(conn, token_hash)
    if reset is None:
        return "Invalid or expired reset link"

    if new_password != confirm_new_password:
        return "New passwords don't match"

    await settings_q.update_password(conn, reset["user_id"], hash_password(new_password))
    await resets_q.mark_used(conn, reset["id"])
    return "Password reset"
