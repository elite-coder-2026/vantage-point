# Issues

## 1. Missing `email-validator` dependency

`app/schemas/users.py` uses Pydantic's `EmailStr`, which requires the
`email-validator` package at import time. It was never declared as a
project dependency, so the app failed to import with:

```
ImportError: email-validator is not installed, run `pip install 'pydantic[email]'`
```

**Fix:** added `email-validator>=2.0` to `pyproject.toml`, regenerated
`uv.lock` and `requirements.txt`, and installed it into the project venv.

## 2. `POST /posts` route collision (JSON API vs. HTML form)

`app/routers/pages.py` already had `POST /posts` as an HTML form handler
(the "What's happening?" box on the feed, form-urlencoded). When
`app/routers/posts.py` was rewritten to add a JSON API at the same path
(`POST /posts` accepting a `TextPostCreate` JSON body), and `posts.router`
is included before `pages.router` in `app/main.py`, the JSON route silently
shadowed the form route. Submitting the feed's post box then hit the JSON
endpoint with form data instead, failing with:

```json
{"detail":[{"type":"model_attributes_type","loc":["body"],"msg":"Input should be a valid dictionary or object to extract fields from","input":"body=testing"}]}
```

**Fix:** moved the HTML form handler to `POST /posts/new` (matching the
distinct-path convention already used elsewhere for page-form vs. JSON-API
pairs, e.g. `/settings/update-password` vs. `/settings/password`), and
updated `app/templates/feed.html`'s form `action` to match.

## 3. No `requirements.txt`

The project only had `pyproject.toml` (managed via `uv`). For running with
a plain `venv`/`pip` workflow, exported one with
`uv export --no-hashes --format requirements-txt -o requirements.txt`.
Needs to be regenerated (same command) if dependencies change.

## 4. No `.env` / missing `VP_DATABASE_URL`

`app/config.py`'s `Settings` requires `database_url` (`VP_DATABASE_URL` env
var) with no default, so the app failed at startup with:

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
database_url
  Field required [type=missing, input_value={}, input_type=dict]
```

**Fix:** created a local Postgres database (`createdb vantage_point`) and a
`.env` file with `VP_DATABASE_URL=postgresql://<user>@localhost/vantage_point`.
`.env` is local-only (not committed) — anyone else running this project
needs to create their own.

## 5. Migrations were never applied

There's no migration runner in this project — `migrations/*.sql` must be
applied by hand, in order, against the target database. None had been run
against the local dev database yet.

**Fix:** applied all migration files in order:

```
for f in migrations/*.sql; do psql -d vantage_point -f "$f" -v ON_ERROR_STOP=1; done
```

## 6. Local environment confusion (not a code bug)

Several run failures during setup were caused by the shell resolving
`python3`/`pip`/`uvicorn` to the wrong interpreter (Homebrew's system
Python, then a `python.org` install) instead of the project's `venv`,
because `source venv/bin/activate` wasn't taking effect in the shell being
used. Worked around by invoking the venv's binaries directly
(`./venv/bin/python3 -m uvicorn ...`, `./venv/bin/python3 -m pip ...`),
which doesn't depend on `PATH`/activation at all.

## 7. No mount for uploaded media

Post image/video/audio/document uploads (`app/posts.py`) are saved to
`settings.media_storage_path`, but nothing served that directory over
HTTP, so uploaded files' URLs would 404.

**Fix:** mounted `settings.media_base_url` (`/media`) to
`settings.media_storage_path` as static files in `app/main.py`.

## 8. Avatar upload/serving didn't exist (RESOLVED)

`config.py` declared `avatar_storage_path` / `avatar_base_url` and
`users.avatar_path` existed as a column, but none of it was wired up: no
upload endpoint, no mount serving that directory, and `UserPublic`
responses didn't expose the field.

**Fix:** added `app/avatar.py` (upload validation/storage + URL helper),
`POST /users/me/avatar` in `app/routers/users.py`, an `avatar_path` field
on `UserPublic`, and a static mount for `avatar_base_url` in
`app/main.py`. Verified: server starts and `/users/me/avatar` is a live
route in the OpenAPI schema.

## 9. Notifications were created but never visible (RESOLVED)

`app/notify.py`/`app/queries/notify.py` already existed and were firing
correctly (likes, comments, shares, tags, follows all created notification
rows), but there was no route, no page, and no nav link to ever see them.

**Fix:** added `app/routers/notify.py` (JSON API), `app/templates/notifications.html`,
a `GET /notifications` page + `POST /notifications/clear` in
`app/routers/pages.py`, and a nav link in `base.html`. Hit the same
route-collision bug as issue 2 during this fix (JSON `GET /notifications`
shadowed the HTML page since `notify.router` is included before
`pages.router`) — moved the JSON list endpoint to `GET /notifications/list`
to resolve it. Verified against a running server.
