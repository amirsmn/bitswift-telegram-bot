import aiosqlite

from typing import Dict, List, Union


DB_NAME = "thresholds.db"


async def init_db() -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS thresholds (
            user_id INTEGER,
            coin TEXT,
            threshold REAL,
            PRIMARY KEY (user_id, coin)
        )
        """)
        await db.commit()


async def add_threshold(user_id: int, coin: str, threshold: float) -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR REPLACE INTO thresholds (user_id, coin, threshold) VALUES (?, ?, ?)",
            (user_id, coin, threshold)
        )
        await db.commit()


async def get_thresholds(user_id: int) -> Dict[str, float]:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute(
            "SELECT coin, threshold FROM thresholds WHERE user_id = ?",
            (user_id,)
        ) as cursor:
           return dict(await cursor.fetchall())


async def del_threshold(user_id: int, coin: str) -> None:
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "DELETE FROM thresholds WHERE user_id = ? AND coin = ?",
            (user_id, coin)
        )
        await db.commit()


async def fetch_all() -> List[Dict[str, Union[int, str, float]]]:
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT * FROM thresholds") as cursor:
           return [
               {
                   "user_id": user_id,
                   "coin": coin,
                   "threshold": threshold
                }
               for user_id, coin, threshold in await cursor.fetchall()
           ]
