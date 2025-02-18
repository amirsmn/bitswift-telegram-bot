import asyncio
import database.database as db
import bot.services.prices as prices_service

from aiogram import Bot


async def check_thresholds(bot: Bot, update_after: int) -> None:
    while True:
        prices = prices_service.latest_prices

        if prices:
            for user in await db.fetch_all():
                try:
                    if prices[user["coin"]][0] >= user["threshold"]:
                        await bot.send_message(
                            chat_id=user["user_id"],
                            text=f"🚨 The price of {user["coin"]} has reached your threshold of ${user["threshold"]}!"
                        )
                except (KeyError, IndexError):
                    continue

        await asyncio.sleep(update_after)
