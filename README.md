# Vantage Point

A social-networking web app built with FastAPI, PostgreSQL, and server-rendered
Jinja2 templates. Supports accounts, follows, groups, multi-type posts (text,
image, video, audio, document, location, link), likes, comments, shares,
tags, mentions, hashtags, bookmarks, notifications, avatars, and password
reset via email.

## Languages used

- **Python** — backend (FastAPI app, business logic, database queries)
- **SQL** — PostgreSQL migrations (`migrations/*.sql`)
- **HTML** — Jinja2 templates (`app/templates/`)
- **CSS** — styling (`app/static/style.css`)
- **JavaScript** — client-side UI toggles (`app/static/app.js`)
- **TOML** — project/dependency config (`pyproject.toml`)
- **Markdown** — documentation (this file, `issues.md`)

## Project layout

```
app/
  main.py            FastAPI app setup, static mounts, router registration
  config.py          Settings (env-configured via VP_ prefix)
  db.py               Database connection pool
  auth.py             Password hashing, session tokens
  posts.py            Post business logic (creation, feed, listings)
  comments.py         Comment business logic
  likes.py            Like business logic (posts + comments)
  shares.py           Share business logic
  notify.py           Notification business logic
  settings.py         Account settings business logic (privacy, blocking)
  forgot_password.py  Password reset business logic
  avatar.py           Avatar upload/storage
  queries/            Raw parameterized SQL per domain
  routers/            FastAPI routes (JSON API + HTML pages)
  schemas/            Pydantic request/response models
  templates/          Jinja2 HTML templates
  static/             CSS/JS assets
migrations/           Ordered SQL migration files (applied by hand)
```

## Setup

### 1. Prerequisites

- Python 3.11+
- PostgreSQL, running locally (or reachable via a connection string)

### 2. Install dependencies

Using `uv` (recommended, matches `pyproject.toml`/`uv.lock`):

```
uv sync
```

Or with plain `pip`:

```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Create the database

```
createdb vantage_point
```

### 4. Apply migrations

There's no migration runner — apply the SQL files by hand, in order:

```
for f in migrations/*.sql; do psql -d vantage_point -f "$f" -v ON_ERROR_STOP=1; done
```

### 5. Configure environment

Create a `.env` file in the project root:

```
VP_DATABASE_URL=postgresql://<user>@localhost/vantage_point
```

Everything else in `app/config.py` has a default and is optional (SMTP
settings are only needed for the forgot-password email flow).

### 6. Run

```
uvicorn app.main:app --reload
```

(or `./venv/bin/python3 -m uvicorn app.main:app --reload` if not using an
activated venv)

Then open `http://127.0.0.1:8000/register`.

## Notes

See `issues.md` for a log of setup/runtime issues encountered while
getting this project running and how each was resolved.
