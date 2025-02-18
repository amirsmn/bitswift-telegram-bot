import bot.services.prices as prices_service
import database.database as db

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext


router = Router()


############# States #############

class AlertStates(StatesGroup):
    waiting_for_coin = State()
    waiting_for_threshold = State()


############# Keyboards #############

def main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Prices", callback_data="prices"),
                InlineKeyboardButton(text="Alerts", callback_data="alerts")
            ],
            [
                InlineKeyboardButton(text="History", callback_data="history"),
                InlineKeyboardButton(text="My Account", callback_data="account")
            ]
        ]
    )


def go_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Back to the Menu", callback_data="go_main_kb")]
        ]
    )


def coins_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="BTC", callback_data="btc_coin"),
                InlineKeyboardButton(text="ETH", callback_data="eth_coin")
            ],
            [
                InlineKeyboardButton(text="TRX", callback_data="trx_coin"),
                InlineKeyboardButton(text="USDT", callback_data="usdt_coin")
            ]
        ]
    )


def go_coins_kb(*, edit_msg: bool = True) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Choose another Coin", callback_data=f"go_coins_kb_{int(edit_msg)}")]
        ]
    )


def del_thresholds_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Delete Threshold", callback_data="del_thresholds")]
        ]
    )


def merge_keyboards(*keyboards: InlineKeyboardMarkup) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            button
            for kb in keyboards
            for button in kb.inline_keyboard
        ]
    )


############# Commands #############

@router.message(Command("start"))
async def cmd_start(msg: types.Message) -> None:
    await msg.answer(
        text=(
            "🚀 *Welcome to BitSwift Bot!*\n\n"
            "Track real-time prices for *BTC, ETH, USDT, and TRON* and set custom price alerts.\n\n"
            "📊 Live price updates\n🚨 Custom alerts\n⚡ Fast & reliable\n\n"
        ),
        parse_mode="Markdown",
        reply_markup=main_kb()
    )


############# Callback Query #############

@router.callback_query(F.data == "go_main_kb")
async def cb_go_main_kb(query: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await query.message.edit_text(text="You can use the buttons below 👇", reply_markup=main_kb())


@router.callback_query(F.data.startswith("go_coins_kb"))
async def foo(query: types.CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AlertStates.waiting_for_coin)

    answer = "Select a coin to set a threshold and get notified 📢 You can also delete the threshold for a coin."

    if query.data[-1] == "1":
        await query.message.edit_text(
            text=answer,
            reply_markup=merge_keyboards(coins_menu(), go_main_kb())
        )
    else:
        await query.message.answer(
            text=answer,
            reply_markup=merge_keyboards(coins_menu(), go_main_kb())
        )


@router.callback_query(F.data == "prices")
async def show_prices(query: types.CallbackQuery) -> None:
    await query.message.edit_text(text=prices_service.formatted_prices(), reply_markup=go_main_kb())


@router.callback_query(F.data == "alerts")
async def select_coin(query: types.CallbackQuery, state: FSMContext) -> None:
    await query.message.edit_text(
        text="Select a coin to set a threshold and get notified 📢 You can also delete the threshold for a coin.",
        reply_markup=merge_keyboards(coins_menu(), go_main_kb())
    )
    await state.set_state(AlertStates.waiting_for_coin)


@router.callback_query(F.data == "account")
async def show_account(query: types.CallbackQuery) -> None:
    thresholds = await db.get_thresholds(user_id=query.from_user.id)
    answer = f"Hello *{query.from_user.first_name}*\n\n*- Your Thresholds List -*\n"

    for coin, threshold in thresholds.items():
        answer += f"*{coin}* -> ${threshold}\n"        

    await query.message.edit_text(text=answer, parse_mode="Markdown", reply_markup=go_main_kb())


@router.callback_query(F.data == "del_thresholds")
async def del_threshold(query: types.CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()

    coin = data["selected_coin"]
    thresholds = await db.get_thresholds(user_id=query.from_user.id)

    if thresholds.get(coin):
        await db.del_threshold(user_id=query.from_user.id, coin=coin)
        answer = f"Threshold has been deleted successfully for {coin}"
    else:
        answer = f"There is no threshold for {coin}"

    await query.message.answer(text=answer, reply_markup=go_coins_kb(edit_msg=False))


############# States Handling #############

@router.callback_query(AlertStates.waiting_for_coin)
async def ask_threshold(query: types.CallbackQuery, state: FSMContext):
    coin = query.data.replace("_coin", "").upper()
    await state.update_data(selected_coin=coin)
    await query.message.edit_text(
        text=f"{prices_service.get_price_offline(coin=coin)}\nSend the threshold price for {coin}:",
        reply_markup=merge_keyboards(del_thresholds_kb(), go_coins_kb())
    )
    await state.set_state(AlertStates.waiting_for_threshold)


@router.message(AlertStates.waiting_for_threshold)
async def set_alert(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    coin = data["selected_coin"]

    try:
        threshold = float(msg.text)
        if threshold <= 0:
            raise ValueError

        await db.add_threshold(user_id=msg.from_user.id, coin=coin, threshold=threshold)

        await msg.answer(
            text=f"✅ Alert set for {coin} at ${threshold}!",
            reply_markup=go_coins_kb(edit_msg=False)
        )
        await state.clear()

    except ValueError:
        await msg.answer(
            text="❌ Invalid number! Please send a valid number greater than 0...",
            reply_markup=go_coins_kb()
        )
