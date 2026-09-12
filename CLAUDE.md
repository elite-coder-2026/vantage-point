Project Overview

Vantage Point is a social app being built by porting an existing PHP codebase (Instagram-like functionality) to Python. This is a port, not a clone — preserve existing behavior/logic unless explicitly told to change it.

Source codebase includes a universal class handling:

Login / session management
Follow system
Private account logic
Online-status tracking
Tech Stack
Target language: Python (porting from PHP)
Backend framework: [FILL IN — e.g. FastAPI / Flask / Django]
Database: [FILL IN — e.g. PostgreSQL, same schema as PHP version or redesigned?]
Frontend: [FILL IN — if applicable]
Porting Conventions
Preserve original logic and edge-case behavior from the PHP universal class unless told otherwise — this is a faithful port first, refactor second.
Flag (don't silently fix) any PHP idioms that don't map cleanly to Python (e.g. loose typing, array/object duck-typing, magic methods).
Keep session/auth semantics equivalent to the original unless asked to modernize them.
Code Style
Async arrow functions only for any JS/Node.js code in this repo — never async function declarations.
[FILL IN Python style conventions: type hints? black/ruff? naming conventions?]
Architecture Notes
[FILL IN: how follow system, private accounts, and online status map to the new Python data model / API endpoints]
What NOT to do
Don't invent new product features unless asked — this phase is porting existing PHP functionality.
Don't restructure the data model without flagging it first, since it may break parity with the original app's behavior.
Open Questions / TODO
 Confirm target backend framework
 Confirm database choice
 Map out universal class methods → new module structure