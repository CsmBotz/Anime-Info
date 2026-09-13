# PROMPT.md — Build Loop

A phase-gated prompt for driving an AI coding assistant through `FEATURES.md` one phase at a time. "Loop" refers to the per-phase cycle below, not a literal infinite loop.

## How to use

Paste the block below into your assistant at the start of a session. It builds one phase, then stops so you can review before the next.

```
You are building a Telegram anime info bot. Stack: PyroFork, MongoDB
(3 clients — users_db, bot_db, cache_db, per STRUCTURE.md), FastAPI
for the Mini App backend. Follow STRUCTURE.md exactly for file layout.

Build only the current unchecked phase in FEATURES.md — do not implement
future-phase features early, even if related code is nearby.

AniList OAuth is deferred (see FEATURES.md → Deferred). If a task in the
current phase touches the Mini App or watchlist and would normally need
a real AniList account connection, use bot-native watchlist data instead
and leave bot/handlers/anilist_auth/ as an unimplemented stub. Do not
build it out even if it looks like a small addition.

After writing code for the phase:
1. Run it, fix errors until it starts cleanly.
2. Test each new command/handler manually against real data.
3. Check SECURITY.md for anything this phase touches before marking it done.
4. Update docs/ideas.md with anything you noticed that's out of scope —
   don't pull it into the current phase.
5. Stop and report what was built — do not silently continue to the next phase.
```

## Per-phase loop

1. Pick the next unchecked item in `FEATURES.md`.
2. Implement it in its own handler file — don't bloat `main.py`.
3. Test in isolation (unit test where the logic allows it, manual test against live data otherwise).
4. Check the item against `SECURITY.md` — most features map to at least one line in there.
5. Confirm which of the 3 Mongo clients the change touches, per `STRUCTURE.md` — don't write logic that assumes two of them are co-located.
6. Check the box, commit, move to the next item.

## Definition of done (applies to every item)

- Starts cleanly with no unhandled startup errors.
- Manually tested against real data, not just a happy-path mock.
- Matching `/help` entry exists if it's a user-facing command (see `STRUCTURE.md → User-Facing Conventions`).
- Relevant `SECURITY.md` items addressed, not just read.
- Nothing from a later phase snuck in.