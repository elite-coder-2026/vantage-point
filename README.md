# Vantage Point

> **High-Performance Social Networking Engine**  
> Built with **FastAPI**, **PostgreSQL**, raw parameterized SQL queries, and server-rendered **Jinja2** templates.

[![Python Version](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Database](https://img.shields.io/badge/database-PostgreSQL-blue.svg)](https://www.postgresql.org/)
[![Framework](https://img.shields.io/badge/framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-informational.svg)](LICENSE)

**Vantage Point** is a lightweight, full-featured social networking web application designed around direct database interactions, clean system architecture, and minimal frontend overhead. It completely eschews heavy ORM abstractions in favor of high-throughput, raw parameterized SQL execution directly against PostgreSQL.

---

## Key Capabilities & Features

* **Multi-Format Content Streams:** Complete support for publishing, indexing, and rendering text, high-resolution images, video streams, audio files, documents, geolocated pins, and external link embeds.
* **Social Graph Architecture:** Built-in engine for user accounts, bidirectional follows, custom user groups, privacy blocking, and account-level permissions.
* **Interaction Engine:** Fast thread processing for likes, nested comments, post re-shares, custom bookmarks, and user mentions/hashtags.
* **Notification Pipeline:** Real-time event notifications for user activity, profile avatars, and background email password resets via SMTP integration.
* **Zero-ORM Performance:** All data queries are maintained as direct, optimized SQL files in `app/queries/` to ensure predictable query execution plans and minimal connection pool overhead.

---

## Tech Stack & Architecture

| Layer | Technology | Key Responsibility |
| :--- | :--- | :--- |
| **Backend API** | Python 3.11+ / FastAPI | Asynchronous request handling, session authentication, routing |
| **Database** | PostgreSQL | Raw parameterized SQL execution, custom migration scripts |
| **Templating** | Jinja2 / HTML5 | Server-side HTML generation for ultra-low latency page loads |
| **Styles & UI** | CSS3 / JavaScript (ES6) | Lightweight asset pipeline and async UI interaction toggles |
| **Package Manager**| `uv` / `pip` | Deterministic dependency resolution via `pyproject.toml` |

---

## Project Layout

```text
app/
├── main.py            # FastAPI app setup, static mounts, router registration
├── config.py          # Environment settings (prefixed via VP_)
├── db.py              # PostgreSQL connection pool allocation
├── auth.py            # Password hashing, PBKDF2/argon2, session tokens
├── posts.py           # Feed aggregation, creation pipelines, listings
├── comments.py        # Threaded comment tree processing
├── likes.py           # Atomic like/reaction operations
├── shares.py          # Distribution and repost logic
├── notify.py         # Event notification handlers
├── settings.py       # Account privacy and blocklist controls
├── forgot_password.py # Secure token generation & SMTP handlers
├── avatar.py          # Multi-type media file storage & avatar pipeline
├── queries/           # Pure parameterized SQL statements per domain
├── routers/           # FastAPI route definitions (REST JSON API + HTML renderers)
├── schemas/           # Pydantic schema validation & data parsing
├── templates/         # Server-rendered Jinja2 templates
└── static/            # Native CSS and vanilla JS assets
migrations/            # Serialized raw SQL migration scripts