#!/usr/bin/env python3
"""
Periodic background cron script to refresh filler dataset and check episode release notifications.
"""
import asyncio
from bot.fetchers.anilist import AniListFetcher
from bot.db.clients import db_clients
from bot.db.users_repo import UsersRepo
from bot.utils.logging import get_logger

logger = get_logger(__name__)

async def notify_new_episodes():
    logger.info("Running episode release notification cron job...")
    await db_clients.init_clients()
    schedules = await AniListFetcher.get_airing_schedule(page=1, per_page=10)
    for sched in schedules:
        media = sched.get("media", {})
        anime_id = media.get("id")
        ep = sched.get("episode")
        title = media.get("title", {}).get("english") or media.get("title", {}).get("romaji")
        logger.info(f"Notification check: {title} episode {ep} airing at {sched.get('airingAt')}")

def main():
    asyncio.run(notify_new_episodes())

if __name__ == "__main__":
    main()

