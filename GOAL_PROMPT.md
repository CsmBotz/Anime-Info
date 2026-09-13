# Goal Prompt — Build Anime Info Bot (All Phases)

> Copy-paste the content inside the ``` block into `/goal` command.

---

```
You are building a complete Telegram anime info bot from scratch in one session.
Do NOT explain steps — just write code, fix errors, move on. Minimize commentary.

━━━ STACK ━━━
PyroFork · MongoDB (3 free-tier clusters) · FastAPI (Mini App backend) · Static HTML/CSS/JS (Mini App frontend) · ffmpeg (subprocess, never shell=True) · Python 3.11+ · Deploy target: Render free tier.

━━━ FOLDER LAYOUT (follow exactly) ━━━
anime-info-bot/
├── bot/
│   ├── main.py                  # client init, handler registration, startup env validation
│   ├── config.py                # env vars, 3 Mongo URIs, API keys — validated at startup, fail fast
│   ├── handlers/
│   │   ├── common/              # /start /help, catch-all error handler (correlation ID in user msg + log)
│   │   ├── info/                # /anime /manga /character /studio /schedule
│   │   ├── inline/              # inline_query — trending on empty query, paginated results
│   │   ├── watchlist/           # add/remove/list, favorites, tracker (+1 episode button)
│   │   ├── image_search/        # trace.moe photo handler, per-user cooldown
│   │   ├── media_tools/         # intro/outro merge (video+mp3), ffprobe validation, semaphore(1-2), queue feedback
│   │   └── anilist_auth/        # STUB ONLY — __init__.py with pass, nothing else
│   ├── fetchers/
│   │   ├── anilist.py           # GraphQL client (filter adult content by default)
│   │   ├── tracemoe.py
│   │   └── filler_list.py       # static/scraped dataset loader
│   ├── db/
│   │   ├── clients.py           # 3 MongoClient instances, lazy connect, one per process, retry/backoff on cold start
│   │   ├── users_repo.py        # → users_db (unique index user_id, compound index user_id+anime_id on watchlist)
│   │   ├── bot_repo.py          # → bot_db (config, feature flags, job state)
│   │   └── cache_repo.py        # → cache_db (TTL-indexed API responses, no PII, safe to wipe)
│   ├── media/
│   │   ├── ffmpeg_utils.py      # subprocess wrapper, timeout, ffprobe type check, sanitized filenames, cleanup tmp/
│   │   └── tmp/                 # .gitkeep — scratch dir wiped after every job
│   └── utils/
│       ├── logging.py           # structured logger (key=value or JSON), no bare print()
│       ├── decorators.py        # per-user cooldown/rate-limit decorator (tells user wait time)
│       └── formatting.py        # shared templates (title/status/score/synopsis/poster), Markdown/HTML escaping
├── webapp/
│   ├── backend/                 # FastAPI — initData HMAC validation (reject stale >24h), watchlist CRUD API, CORS locked to Telegram WebView
│   └── frontend/                # Static Mini App UI (3 screens below), no build step
├── tests/
│   ├── fixtures/                # recorded AniList responses
│   └── test_*.py                # pytest, mocked fetchers, smoke test (import all handlers, boot with fake token)
├── scripts/
│   └── refresh_filler_list.py
├── docs/
│   └── ideas.md                 # scope-creep parking lot
├── .env.example                 # every key with placeholder, git-ignored .env holds real values
├── requirements.txt             # pinned versions
├── render.yaml                  # env vars by name, values set in dashboard
└── README.md

━━━ 3 MONGO DBs (separate free-tier clusters = 512MB × 3) ━━━
• users_db — durable, small, never lose data. Backup discipline (Atlas snapshots or periodic export). Contains watchlist, favorites, tracker, user prefs. Indexes: unique user_id, compound user_id+anime_id.
• bot_db — config/state, feature flags, job state.
• cache_db — TTL-indexed API responses. Disposable. No PII.
Connect lazily. One client/process. Short retry/backoff on first query after idle (Render sleeps + Atlas free pauses).
Never string-interpolate user input into Mongo queries. Parameterized filter dicts only. No $where.

━━━ FEATURES TO BUILD (all phases, in order) ━━━

PHASE 1 — MVP:
1. /anime /manga /character /studio lookup via AniList GraphQL → formatted card (title, status, score, truncated synopsis, poster), "more results" pagination via inline keyboard if ambiguous.
2. Inline query search — results as user types, trending titles on empty query, works in any chat.
3. Watchlist — add/remove/list via MongoDB users_db, per user. Confirmation messages. Paginated /watchlist view.

PHASE 2:
4. Favorites — /favorites list, quick-toggle from any anime card.
5. Tracker — episode/chapter progress + status, inline "+1" button to bump without retyping.
6. Image → anime search via trace.moe — send screenshot, get anime+episode+timestamp. Per-user cooldown.
7. Filler episode lookup — /filler <anime> returns filler/canon breakdown from scraped dataset.

PHASE 3 — Mini App & Notifications:
8. Telegram Mini App (static HTML/CSS/JS frontend + FastAPI backend):
   - Backend: validate initData HMAC every request, reject auth_date >24h, re-derive identity from initData (never trust client fields), never log raw initData, CORS locked to Telegram WebView origin.
   - Screen 1 — Home/Discover: search bar (same AniList query as /anime), featured carousel (from cache_db trending), "Recommended" grid with Watchlist/Favorite/Progress badges.
   - Screen 2 — Browse/Catalog: filter tabs (All/Popular/New/Genre), trending shelf then full catalog alphabetically grouped with sticky letter headers, poster tiles with genre tags + status badges.
   - Screen 3 — Detail: full poster/banner, title, synopsis, score, status, episodes. Action row: Add to Watchlist / Mark Watched / Add to Favorites. If already on watchlist, show +1 episode / mark complete instead.
   - NOT building: view counts, comment counts, mail inbox, requests badge.
   - Data source: reads from users_db + bot_db only, no new collections.
9. Episode release notifications — batched cron job (not per-request polling). Message user when tracked show's next ep airs.

PHASE 4 — Media Tools:
10. Add intro to video, add outro to video, add intro/outro to mp3.
    - ffprobe format/codec check before merge.
    - File size + duration caps enforced before processing.
    - Validate type via ffprobe, not extension.
    - subprocess with arg list, never shell=True. Sanitize/discard user filenames (path traversal).
    - Hard timeout on ffmpeg.
    - asyncio.Semaphore(1-2) concurrency cap. Queue position feedback to user.
    - Always clean bot/media/tmp/ after every job (success, failure, timeout, crash).
    - Clear errors ("unsupported format" / "file too long") not silent failures.

ALSO BUILD:
11. /deleteme — purge user's users_db entry (user data control).
12. /help — auto-updated entry for every user-facing command.
13. Register command list with BotFather (setMyCommands) as part of startup.

━━━ SECURITY RULES (enforce throughout) ━━━
• Secrets: env vars only, .env git-ignored, .env.example with placeholders. render.yaml references by name.
• Escape user text before embedding in Markdown/HTML Telegram messages.
• AniList adult content: filter by default.
• Rate limiting: per-user cooldown on image search + media tools. Handle PyroFork FloodWait with backoff.
• No raw exceptions in chat — friendly message + correlation ID, real error logged server-side.
• Cooldown replies tell user how long to wait.
• Pin deps in requirements.txt.
• anilist_auth/ is a stub — do NOT implement OAuth.

━━━ CONVENTIONS ━━━
• Each handler in its own file — don't bloat main.py.
• One catch-all error handler wrapping dispatch.
• Structured logs (key=value or JSON).
• Paginate anything >5 results with inline keyboard buttons.
• Consistent response template: title, type/status, score, truncated synopsis + "Read more" link, poster.
• Inline mode never returns blank on empty query — show trending/popular.
• tests/fixtures/ for recorded API responses. Smoke test: import all handlers, boot with fake token.

━━━ EXECUTION RULES ━━━
• Write all files. Don't stop between phases.
• Don't explain code. Just create files and move on.
• After all code is written: run it, fix startup errors, verify imports.
• When done, report what was built (brief list, not per-file narration).
```

