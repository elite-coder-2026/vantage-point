"""
Ported from a PHP `time` class's timeAgo()/normalTime() methods.

Dropped the original's unconditional `$time = ($time + 4*60*60) + 30*60`
offset before bucketing — that's a fixed 4.5-hour correction for a
timezone mismatch specific to the original server (PHP's configured
timezone vs. MySQL's now()), not a rule that means anything against this
project's UTC-stored TIMESTAMPTZ columns. Keeping it would make every
timestamp here read 4.5 hours further in the past than it actually is.

The `$time == 1` on the original's <=60s branch (rather than <=1) is
preserved as-is: only exactly 1 second elapsed reads "Just now"; 0
seconds and 2-60 seconds all read "N secs".
"""

from datetime import datetime, timezone

_MINUTE = 60
_HOUR = 3600
_DAY = 86400
_WEEK = 604800
_MONTH = 2600640
_YEAR = 31207680


def time_ago(dt: datetime) -> str:
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    seconds = max(0, int((now - dt).total_seconds()))

    if seconds <= _MINUTE:
        return "Just now" if seconds == 1 else f"{seconds} secs"
    if seconds < _HOUR:
        minutes = round(seconds / _MINUTE)
        return "1 min" if minutes == 1 else f"{minutes} mins"
    if seconds < _DAY:
        hours = round(seconds / _HOUR)
        return "1 hour" if hours == 1 else f"{hours} hours"
    if seconds < _WEEK:
        days = round(seconds / _DAY)
        return "1 day" if days == 1 else f"{days} days"
    if seconds < _MONTH:
        weeks = round(seconds / _WEEK)
        return "1 week" if weeks == 1 else f"{weeks} weeks"
    if seconds < _YEAR:
        months = round(seconds / _MONTH)
        return "1 month" if months == 1 else f"{months} months"

    years = round(seconds / _YEAR)
    return "1 year" if years == 1 else f"{years} years"


def normal_time(dt: datetime) -> str:
    date_part = dt.strftime("%d-%B-%Y %I:%M:%S")
    am_pm = dt.strftime("%p").lower()
    return f"{date_part} {am_pm}"
