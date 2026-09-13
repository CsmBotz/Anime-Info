import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bot.config import USERS_MONGO_URI, BOT_MONGO_URI, CACHE_MONGO_URI
from bot.utils.logging import get_logger

logger = get_logger(__name__)

class MongoClients:
    _instance = None

    def __init__(self):
        self.users_client = None
        self.bot_client = None
        self.cache_client = None
        self.users_db = None
        self.bot_db = None
        self.cache_db = None
        self._initialized = False

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = MongoClients()
        return cls._instance

    async def init_clients(self):
        if self._initialized:
            return
        
        # Lazy connection with retry logic
        for attempt in range(3):
            try:
                if USERS_MONGO_URI:
                    self.users_client = AsyncIOMotorClient(USERS_MONGO_URI, serverSelectionTimeoutMS=5000)
                    self.users_db = self.users_client.get_database()
                if BOT_MONGO_URI:
                    self.bot_client = AsyncIOMotorClient(BOT_MONGO_URI, serverSelectionTimeoutMS=5000)
                    self.bot_db = self.bot_client.get_database()
                if CACHE_MONGO_URI:
                    self.cache_client = AsyncIOMotorClient(CACHE_MONGO_URI, serverSelectionTimeoutMS=5000)
                    self.cache_db = self.cache_client.get_database()
                
                await self.setup_indexes()
                self._initialized = True
                logger.info("MongoDB clients initialized successfully.")
                break
            except Exception as e:
                logger.warning(f"Mongo init attempt {attempt+1} failed: {e}")
                if attempt < 2:
                    await asyncio.sleep(2)
                else:
                    logger.error("Failed to connect to MongoDB after 3 attempts.")

    async def setup_indexes(self):
        if self.users_db is not None:
            # unique index on users.user_id
            await self.users_db.users.create_index("user_id", unique=True)
            # compound index on watchlist user_id + anime_id
            await self.users_db.watchlist.create_index([("user_id", 1), ("anime_id", 1)], unique=True)
            await self.users_db.favorites.create_index([("user_id", 1), ("anime_id", 1)], unique=True)
        if self.cache_db is not None:
            # TTL index on cache collection
            await self.cache_db.api_cache.create_index("created_at", expireAfterSeconds=86400)

db_clients = MongoClients.get_instance()

