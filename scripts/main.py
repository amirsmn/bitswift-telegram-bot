import asyncio
import dotenv
import os
import bot.services.prices as prices_service
import bot.services.alerts as alerts_service
import database.database as db

from aiogram import Dispatcher, Bot
from bot.handlers.handlers import router


UPDATE_AFTER = 300


async def main() -> None:
    dotenv.load_dotenv()

    dp = Dispatcher()
    bot = Bot(token=os.getenv("TOKEN_API", ""))

    asyncio.create_task(prices_service.update_prices(update_after=UPDATE_AFTER))
    # Wait for prices to update
    await asyncio.sleep(5)
    asyncio.create_task(alerts_service.check_thresholds(bot=bot, update_after=UPDATE_AFTER))

    await db.init_db()

    dp.include_router(router=router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
