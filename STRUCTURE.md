# Project Structure — Anime Info Bot

Standalone project. No reused code from CosmicPosterBot — fresh fetchers, its own repo, its own conventions.
SECURITY.md`
> **Naming convention:** root-level docs are UPPERCASE (`STRUCTURE.md`, `SECURITY.md`, `FEATURES.md`, `PROMPT.md`), matching how `README.md` is normally styled, and matching how `PROMPT.md` already refers to them.

## Stack

| Layer | Choice | Why |
|---|---|---|
| Bot framework | PyroFork | Async, actively maintained Pyrogram fork, matches prior experience |
| Database | MongoDB, 3 clusters | See split rationale below |
| Media | ffmpeg (subprocess, not shell) | Standard tool for intro/outro merges |
| Mini App backend | FastAPI | Async, easy `initData` validation, deploys alongside the bot |
| Mini App frontend | Static HTML/CSS/JS | No build step — keeps the free-tier deploy simple |
| Hosting | Render free tier | Target — see constraints below |
| Runtime | Python 3.11+ | Modern async syntax, better error messages |

## Folder Layout

```
anime-info-bot/
├── bot/
│   ├── main.py                     # Client init, handler registration, startup env validation
│   ├── config.py                   # env vars, all 3 Mongo URIs, API keys — validated at startup
│   ├── handlers/
│   │   ├── common/                 # /start, /help, generic error handler
│   │   ├── info/                   # /anime /manga /character /studio /schedule
│   │   ├── inline/                 # inline_query handler
│   │   ├── watchlist/              # add / remove / list, favorites, tracker
│   │   ├── image_search/           # trace.moe photo handler
│   │   ├── media_tools/            # intro/outro merge (video + mp3)
│   │   └── anilist_auth/           # DEFERRED — stub only, see FEATURES.md
│   ├── fetchers/
│   │   ├── anilist.py              # GraphQL client
│   │   ├── jikan.py
│   │   ├── mangadex.py
│   │   ├── tracemoe.py
│   │   └── filler_list.py          # scraped/static dataset loader
│   ├── db/
│   │   ├── clients.py              # 3 MongoClient instances, lazy connect, one per process
│   │   ├── users_repo.py           # → users_db
│   │   ├── bot_repo.py             # → bot_db (config, feature flags, job state)
│   │   └── cache_repo.py           # → cache_db (TTL-indexed API responses)
│   ├── media/
│   │   ├── ffmpeg_utils.py         # subprocess wrapper, timeout, ffprobe validation
│   │   └── tmp/                    # scratch dir, wiped after every job
│   └── utils/
│       ├── logging.py              # structured logger setup
│       ├── decorators.py           # per-user cooldown / rate-limit decorator
│       └── formatting.py           # shared message templates, Markdown/HTML escaping
├── webapp/
│   ├── backend/                    # FastAPI — initData validation, watchlist API (OAuth callback deferred)
│   └── frontend/                   # static Mini App UI — screens per MINI_APP_UX.md
├── tests/
│   ├── fixtures/                   # recorded AniList/Jikan/MangaDex responses
│   └── test_*.py                   # pytest, fetchers mocked — no live-API dependency
├── scripts/
│   └── refresh_filler_list.py      # periodic job
├── docs/
│   └── ideas.md                    # scope-creep parking lot (see FEATURES.md → Backlog)
├── .env.example
├── requirements.txt
├── render.yaml
└── README.md
```

## The 3-MongoDB split — the actual reasoning

- `users_db` — durable, small, must never lose data.
- `bot_db` — config/state, small.
- `cache_db` — AniList/Jikan/MangaDex responses — disposable, TTL-indexed, safe to wipe anytime.

The real win isn't organizational neatness — three separate free-tier clusters multiply your free storage cap (512MB × 3 instead of × 1). The cost is three live connections, which means more baseline RAM on a free Render instance. To keep that in check:

- Connect lazily (on first use, not at import time).
- One client per process, reused across requests — never open a new connection per request.
- Add a short retry/backoff around the first query after an idle period. Render's free tier sleeps, and Mongo Atlas free clusters can pause too, so the first request after a cold start should expect a slow or failed connection and retry once before surfacing an error to the user.
- Minimum indexes on day one: unique index on `users_db.users.user_id`, TTL index on `cache_db` collections, compound index on watchlist lookups (`user_id + anime_id`).

## Config & Secrets

- Validate all required env vars at startup — fail fast with a clear message rather than discovering a missing key mid-request.
- `.env.example` lists every key with a placeholder; `.env` itself is git-ignored.

## User-Facing Conventions

This is the part a real user experiences, so it's worth being deliberate about:

- Register the command list with BotFather (`setMyCommands`) so Telegram's command menu stays in sync with what's actually implemented — update it as part of each phase's "definition of done," not as an afterthought.
- Every command ships with a matching `/help` entry.
- Paginate anything that can return more than ~5 results (search matches, watchlist) with inline keyboard buttons — a wall of text is a bad first impression for a lookup bot.
- Keep one consistent response template: title, type/status, score, a truncated synopsis with a "Read more" link, and a poster image where available.
- Never show a raw exception or stack trace in chat. Catch at the handler level, reply with a short, friendly message, and log the real error server-side.
- Cooldown/rate-limit replies should say how long to wait ("try again in 12s"), not silently drop the message.
- Inline mode should never come back empty on an empty query — show trending/popular titles by default so the first interaction with inline mode isn't a blank result list.

## Error Handling & Logging

- One catch-all error handler wrapping dispatch, not scattered try/excepts per handler.
- Structured logs (key=value or JSON) over bare `print()` — much easier to search in Render's log viewer.
- Tag the user-facing "something went wrong" message with a short correlation ID that also appears in the log line, so a bug report can actually be traced back.

## Testing

- `tests/fixtures/` holds recorded API responses so fetcher tests don't depend on AniList/Jikan/MangaDex being up (or rate-limiting you) during CI.
- A minimal smoke test — import every handler module, boot the app with a fake token — catches the "forgot an import" class of bug before manual testing does.

## Infra Constraint — ffmpeg on Render Free Tier

Intro/outro merging is CPU + disk heavy. Render's free web tier has limited CPU, a small ephemeral disk, and spins down on idle — a merge job can time out mid-request or fill the temp disk if concurrent jobs aren't capped.

- Cap concurrency with an `asyncio.Semaphore` (1–2 jobs at a time) before this ships, not after.
- Give the user queue feedback ("your video is queued — position 2") instead of a silent wait; a merge can take long enough that "nothing happened" reads as broken.

## Deferred Work

`bot/handlers/anilist_auth/` and the OAuth callback in `webapp/backend/` are shown in the layout above but intentionally not implemented yet — see `FEATURES.md → Deferred`. Leave the folder as a stub (or omit it entirely) until that phase is picked back up.