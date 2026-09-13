# Features — Anime Info Bot

Each item notes what the user actually sees, not just the implementation. "Deferred" items are intentionally out of scope for now — `PROMPT.md` tells the build assistant to skip them even if adjacent work makes them look convenient to bundle in.

## Phase 1 — MVP

- [ ] `/anime` `/manga` `/character` `/studio` lookup (AniList GraphQL)
  - User sees: a formatted card (title, status, score, truncated synopsis, poster) for the top match, with "more results" pagination if the query is ambiguous.
- [ ] Inline query search (usable in any chat)
  - User sees: results as they type, in any chat, including groups the bot isn't in; an empty query shows trending titles instead of a blank list.
- [ ] Watchlist: add / remove / list (MongoDB, per user)
  - User sees: a confirmation on add/remove ("Added to your watchlist"), and a paginated `/watchlist` view.

## Phase 2

- [ ] Favorites
  - User sees: a `/favorites` list separate from the general watchlist, with a quick-toggle from any anime card.
- [ ] Tracker (progress + status, manual update)
  - User sees: current episode/chapter progress on the watchlist card, with an inline button to bump it by one without retyping a command.
- [ ] Image → anime search (trace.moe)
  - User sees: send a screenshot, get back the matching anime + episode/timestamp; per-user cooldown applies (see `SECURITY.md`).
- [ ] Filler episode lookup (scraped dataset)
  - User sees: `/filler <anime>` returns a filler/canon episode breakdown.

## Phase 3 — Mini App & Notifications

*(AniList OAuth removed from this phase — see Deferred below. Everything here runs on bot-native data only.)*

- [ ] Telegram Mini App — browsable watchlist/tracker UI
  - User sees: a scrollable UI inside Telegram instead of paginated chat messages, backed by the same `users_db` watchlist data as the bot commands.
  - Screen-by-screen spec: see `MINI_APP_UX.md` (Home/Discover, Browse/Catalog with alphabetical grouping, Detail with watchlist/watched/favorite actions).
- [ ] Episode release notifications (batched cron job, not per-request)
  - User sees: a message when a tracked show's next episode airs, without the bot polling per-user in real time.

## Phase 4 — Media Tools

- [ ] Add intro to video
- [ ] Add outro to video
- [ ] Add intro/outro to mp3
- [ ] ffprobe format/codec check before merge (mismatched codecs are the #1 cause of broken merges)
  - User sees, across all four: upload video/audio + intro or outro clip, get back the merged file; a queue-position message if another job is already running (see `STRUCTURE.md → Infra Constraint`); a clear error ("unsupported format" / "file too long") instead of a silent failure when validation fails.

## Deferred

- [ ] AniList OAuth — real account connect + list sync
  - Paused for now. Revisit after Phase 4 ships. Requirements are documented in `SECURITY.md` so nothing is lost in the meantime; when this resumes, Phase 3's Mini App and tracker gain a "connect your AniList account" upgrade path rather than needing a rebuild.

## Backlog

Anything new you think of mid-build goes in `docs/ideas.md`, not straight into an earlier phase. Every feature pulled into Phase 1–2 pushes the MVP date.