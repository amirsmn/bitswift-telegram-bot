import aiohttp
import asyncio

from typing import Tuple


COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price"

SUPPORTED_COINS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "TRX": "tron",
    "USDT": "tether"
}

latest_prices = {}


async def get_price_online(session: aiohttp.ClientSession, coin: str) -> Tuple:
    try:
        async with session.get(
            COINGECKO_API,
            params={"ids": SUPPORTED_COINS[coin], "vs_currencies": "usd", "include_24hr_change": "true"},
            raise_for_status=True
        ) as response:
            data = await response.json()

            return (
                data.get(SUPPORTED_COINS[coin], {}).get("usd", None),
                data.get(SUPPORTED_COINS[coin], {}).get("usd_24h_change", None)
            )

    except aiohttp.ClientError:
        return ()


async def update_prices(update_after) -> None:
    # may i use a temp var and then: latest_prices = temp if i see any problem in future (race condition)
    async with aiohttp.ClientSession() as session:
        while True:
            global latest_prices
            for coin in SUPPORTED_COINS:
                latest_prices[coin] = await get_price_online(session, coin)

            await asyncio.sleep(update_after)


def formatted_prices() -> str:
    prices = ""
    for coin, price_data in latest_prices.items():
        price = get_price_offline(coin)
        changes = "N/A"

        if price_data and price_data[1] is not None:
            changes = f"{price_data[1]:0.2f}"
            if float(changes) > 0:
                changes = f"{changes}% 🟩"
            elif float(changes):
                changes = f"{abs(float(changes))}% 🟥"
            else:
                changes = "0% ⬜️"

        prices += f"{price} ~ {changes}\n\n"

    return prices


def get_price_offline(coin: str) -> str:
    coin = coin.upper()
    try:
        if latest_prices[coin][0] is None:
            return "N/A"
        else:
            return f"{coin} = ${latest_prices[coin][0]}"
    except:
        return "N/A"
