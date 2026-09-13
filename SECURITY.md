# Security — Anime Info Bot

## Secrets

- Bot token, all 3 Mongo URIs, AniList client secret → env vars only, never committed. `.env` is git-ignored; `.env.example` holds placeholders only.
- `render.yaml` references env vars by name; actual values are set in the Render dashboard, not in the repo.
- If any secret ever leaks (committed by accident, pasted somewhere public), rotate it immediately — regenerate the bot token via BotFather, rotate the Mongo URIs/passwords, rotate the AniList client secret. Don't wait to see if it matters.

## Telegram Mini App

- Every request to the Mini App backend must validate Telegram's `initData` HMAC signature before trusting `user_id`. Unvalidated `initData` means anyone can claim to be any user.
- Reject stale `initData` — check `auth_date` and refuse anything older than a reasonable window (e.g. 24h) to limit replay of a captured payload.
- Keep the backend stateless where possible: re-derive identity from `initData` on every request rather than trusting client-sent user fields.
- Never log the raw `initData` string — it carries the HMAC and user payload together.
- Lock CORS down to Telegram's WebView origin instead of leaving it open.

## AniList OAuth — deferred

OAuth is out of scope for the current build (see `FEATURES.md → Deferred`). Documenting the requirements now so nothing is lost when it's picked back up:

- Validate the `state` param on the callback to block CSRF.
- Store access/refresh tokens in `users_db` only, encrypted at rest if possible — never in `cache_db` or logs.
- Never log tokens, even in debug mode.
- Implement a token refresh flow and a clean "disconnect" path that revokes and deletes the stored token.

Until this resumes, the Mini App and tracker run on bot-native watchlist data only — no real AniList account sync.

## Media Tools (intro/outro) — highest-risk feature

Untrusted user-uploaded video/audio going through ffmpeg:

- Enforce file size + duration caps before processing.
- Validate file type via `ffprobe`, not just the file extension.
- Run ffmpeg via subprocess with an argument list — never `shell=True` — so a spoofed filename can't reach a shell.
- Sanitize or discard user-supplied filenames rather than using them directly in temp file paths, to avoid path traversal.
- Run ffmpeg with a hard timeout; malformed input can otherwise hang indefinitely.
- Cap concurrency (1–2 jobs at a time) — free-tier CPU can't handle parallel merges.
- Always clean `bot/media/tmp/` after every job, success or failure, including on timeout/crash.

## Input Validation & Injection

- Never build MongoDB queries by string-interpolating user input; use parameterized filter dicts and avoid `$where`/server-side JS entirely.
- Escape user-supplied text before embedding it in a Markdown/HTML-formatted Telegram message — unescaped input can break formatting or spoof a link.

## Content

- AniList includes adult-tagged entries — filter by default, offer an explicit opt-in toggle, or risk Telegram flagging the bot.

## Rate Limiting

- Per-user cooldown specifically on image search and media tools — the two handlers expensive enough to be worth abusing for a cheap DoS.
- Respect Telegram's own flood limits too: PyroFork surfaces `FloodWait` — handle it with a backoff, don't retry immediately in a loop.

## Dependency & Supply Chain

- Pin versions in `requirements.txt`.
- Run `pip-audit` (or enable Dependabot) periodically — a hobby project still pulls in real CVEs through transitive dependencies.
- Use an official ffmpeg build rather than an arbitrary third-party binary.

## Data

- `cache_db` — TTL-indexed, no PII, safe to wipe anytime.
- `users_db` — the only store that needs backup discipline. Set up automated snapshots (Atlas free tier supports basic backups) or a periodic export job.
- Give users control over their own data — a `/deleteme` command that purges their `users_db` entry is good practice, and a feature users will genuinely ask for once the bot has any real traffic.