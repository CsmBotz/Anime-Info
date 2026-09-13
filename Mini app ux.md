# Mini App UX — Anime Info Bot

Reference: a competitor app's Discover/Browse flow (screenshot + screen recording provided during planning). Adapted to our own data model — features from the reference with no equivalent in our project are called out and dropped rather than silently copied.

This spec is what Phase 3's "Telegram Mini App — browsable watchlist/tracker UI" item in `FEATURES.md` actually builds. It doesn't add new backend features — every action below already exists as a bot command from Phase 1–2; this is a second UI on top of the same `users_db` collections.

## Screens

### 1. Home / Discover

- Header: bot avatar + name, search bar (`Search anime...`) wired to the same AniList query used by `/anime`.
- Featured carousel: horizontally swipeable cards — poster, title, one-line synopsis, year, dot pagination. Pulls from `cache_db` (trending/popular), not a live call per view.
- **For You**: shelf mixing the user's in-progress tracker items with picks from their favorited genres. This needs light recommendation logic beyond a straight API wrapper — if it doesn't fit Phase 3 cleanly, drop it to `docs/ideas.md` rather than stretching the phase to fit it.
- **Recommended** grid: poster tiles with quick-action badges. Reference used badges like "Requests" / "Comments" — ours map to data we actually have: **Watchlist**, **Favorite**, **Progress (e.g. "12/24")**.

### 2. Browse / Catalog

- Filter tabs: All / Popular / New / Genre — same GraphQL filter params `/anime` already uses server-side, just exposed as UI chips instead of a slash command.
- Scroll order (matches the recording): a trending/curated shelf first, then the full catalog **grouped and sorted alphabetically by title**, with a sticky letter header (A, B, C…) so users can tell where they are mid-scroll.
- Each tile: poster, title, genre tag(s), a status badge (Airing / Popular / Dub available).
- Tap target is the whole poster tile → opens the Detail screen. This is the Mini App equivalent of the "tap to view" affordance shown in the recording.

### 3. Detail

- Full poster/banner, title, synopsis, score, status, episode count.
- Primary action row: **Add to Watchlist**, **Mark as Watched**, **Add to Favorites** — these are the existing Phase 1–2 bot actions, just as buttons instead of commands.
- If the title is already on the user's watchlist, swap "Add to Watchlist" for progress controls (+1 episode / mark complete) — this is the Mini App's version of the tracker's inline "+1" button already planned in Phase 2, not a new feature.

## Intentionally not carried over from the reference

- View counts / comment counts — we're not building a social layer; skip.
- The "Mail" inbox icon — no in-app messaging is planned. If episode-release notifications (Phase 3) later want an in-app inbox instead of a chat message, that's a redesign decision to make then, not something to half-build now.
- The "Requests" badge — no equivalent in our data model; drop until a concrete use shows up.

## Data source

Everything above reads from `bot_db` / `users_db` per `STRUCTURE.md` — no new database, no new endpoint category. It's a UI layer over the watchlist, favorites, and tracker collections already planned for Phase 1–2.