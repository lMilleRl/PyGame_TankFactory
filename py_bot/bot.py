"""Telegram-бот «Диспетчер Цеха» (aiogram 3)."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from . import analytics, session
from .config import ADMIN_ID, BOT_TOKEN, LOG_PATH, SESSIONS_DIR
from .keyboards import back_kb, main_menu_kb
from .session import BotState

logger = logging.getLogger("dispatcher_bot")


def setup_logging() -> None:
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    handler = logging.FileHandler(LOG_PATH, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(handler)
    logger.propagate = False


async def safe_edit(message: Message, text: str, reply_markup=None) -> None:
    try:
        await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as exc:
        # Типичные случаи: message is not modified / message to edit not found.
        if "message is not modified" in str(exc).lower():
            return
        if "message to edit not found" in str(exc).lower() or "message can't be edited" in str(exc).lower():
            await message.answer(text, reply_markup=reply_markup)
            return
        raise


def format_top() -> str:
    rows = analytics.top_by_efficiency(10)
    if not rows:
        return "Топ пуст. Сыграйте партию и сохраните рекорд в scores.csv."
    lines = ["Топ по эффективности конвейера", "метрика: детали / ходы (больше лучше)", ""]
    for i, row in enumerate(rows, start=1):
        lines.append(
            f"{i}. {row.get('player_name', '?')} - {row['efficiency']:.4f} "
            f"({row['parts_assembled']} дет. / {row['turns']} ходов)"
        )
    return "\n".join(lines)


def format_stats(player_name: str) -> str:
    info = analytics.player_stats(player_name)
    if not info["found"]:
        return f"Игрок «{player_name}» не найден в scores.csv."
    return (
        f"Статистика: {info['player_name']}\n"
        f"Игр: {info['games']}\n"
        f"Лучший результат: {info['best_turns']} ходов\n"
        f"Средняя эффективность: {info['avg_efficiency']}\n"
        f"Последняя эффективность: {info['last_efficiency']}"
    )


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def cmd_start(message: Message) -> None:
        data = session.load_session(message.from_user.id)
        session.set_state(message.from_user.id, BotState.MENU)
        text = (
            "Диспетчер Цеха\n"
            "Аналитика игры «Танковый завод».\n"
            "Команды: /top /stats /upload /watch"
        )
        if not data.get("player_name"):
            session.set_state(message.from_user.id, BotState.WAIT_NAME)
            await message.answer(text + "\n\nВведите имя игрока для /stats:")
            return
        await message.answer(text, reply_markup=main_menu_kb())

    @dp.message(Command("top"))
    async def cmd_top(message: Message) -> None:
        await message.answer(format_top(), reply_markup=back_kb())
        logger.info("user=%s /top", message.from_user.id)

    @dp.message(Command("stats"))
    async def cmd_stats(message: Message) -> None:
        data = session.load_session(message.from_user.id)
        name = data.get("player_name") or ""
        if not name:
            session.set_state(message.from_user.id, BotState.WAIT_NAME)
            await message.answer("Сначала введите имя игрока:")
            return
        await message.answer(format_stats(name), reply_markup=back_kb())

    @dp.message(Command("upload"))
    async def cmd_upload(message: Message) -> None:
        session.set_state(message.from_user.id, BotState.UPLOAD)
        await message.answer("Пришлите файл factory_layout.txt (документом).")

    @dp.message(Command("watch"))
    async def cmd_watch(message: Message) -> None:
        data = session.load_session(message.from_user.id)
        data["watch"] = not data.get("watch", False)
        session.save_session(message.from_user.id, data)
        state = "включена" if data["watch"] else "выключена"
        await message.answer(f"Подписка на уведомления {state}.", reply_markup=back_kb())
        logger.info("user=%s watch=%s", message.from_user.id, data["watch"])

    @dp.message(Command("broadcast"))
    async def cmd_broadcast(message: Message, bot: Bot) -> None:
        if message.from_user.id != ADMIN_ID or ADMIN_ID == 0:
            await message.answer("Команда только для администратора.")
            return
        session.set_state(message.from_user.id, BotState.BROADCAST)
        await message.answer("Введите текст рассылки подписчикам /watch:")

    @dp.callback_query(F.data == "menu")
    async def cb_menu(callback: CallbackQuery) -> None:
        await callback.answer()
        session.set_state(callback.from_user.id, BotState.MENU)
        await safe_edit(
            callback.message,
            "Меню диспетчера. Выберите действие:",
            reply_markup=main_menu_kb(),
        )

    @dp.callback_query(F.data == "top")
    async def cb_top(callback: CallbackQuery) -> None:
        await callback.answer()
        await safe_edit(callback.message, format_top(), reply_markup=back_kb())

    @dp.callback_query(F.data == "stats")
    async def cb_stats(callback: CallbackQuery) -> None:
        await callback.answer()
        data = session.load_session(callback.from_user.id)
        name = data.get("player_name") or ""
        if not name:
            session.set_state(callback.from_user.id, BotState.WAIT_NAME)
            await safe_edit(callback.message, "Введите имя игрока сообщением:")
            return
        await safe_edit(callback.message, format_stats(name), reply_markup=back_kb())

    @dp.callback_query(F.data == "upload")
    async def cb_upload(callback: CallbackQuery) -> None:
        await callback.answer()
        session.set_state(callback.from_user.id, BotState.UPLOAD)
        await safe_edit(callback.message, "Пришлите файл layout документом.")

    @dp.callback_query(F.data == "watch")
    async def cb_watch(callback: CallbackQuery) -> None:
        await callback.answer()
        data = session.load_session(callback.from_user.id)
        data["watch"] = not data.get("watch", False)
        session.save_session(callback.from_user.id, data)
        state = "включена" if data["watch"] else "выключена"
        await safe_edit(
            callback.message,
            f"Подписка на уведомления {state}.",
            reply_markup=back_kb(),
        )

    @dp.message(F.document)
    async def on_document(message: Message, bot: Bot) -> None:
        data = session.load_session(message.from_user.id)
        if data.get("state") != BotState.UPLOAD.value:
            return
        file = message.document
        if not file:
            return
        buffer = await bot.download(file)
        text = buffer.read().decode("utf-8", errors="replace")
        ok, info = analytics.validate_layout_text(text)
        data["uploads"] = int(data.get("uploads", 0)) + 1
        data["state"] = BotState.MENU.value
        session.save_session(message.from_user.id, data)
        if ok:
            target = SESSIONS_DIR / f"upload_{message.from_user.id}.txt"
            target.write_text(text, encoding="utf-8")
            await message.answer(f"Layout принят. {info}", reply_markup=main_menu_kb())
            logger.info("user=%s upload ok", message.from_user.id)
        else:
            await message.answer(f"Layout отклонён: {info}", reply_markup=main_menu_kb())
            logger.info("user=%s upload fail: %s", message.from_user.id, info)

    @dp.message(F.text)
    async def on_text(message: Message, bot: Bot) -> None:
        data = session.load_session(message.from_user.id)
        state = data.get("state")
        text = (message.text or "").strip()
        if state == BotState.WAIT_NAME.value:
            data["player_name"] = text[:40]
            data["state"] = BotState.MENU.value
            session.save_session(message.from_user.id, data)
            await message.answer(
                f"Имя сохранено: {data['player_name']}",
                reply_markup=main_menu_kb(),
            )
            return
        if state == BotState.BROADCAST.value:
            if message.from_user.id != ADMIN_ID:
                return
            data["state"] = BotState.MENU.value
            session.save_session(message.from_user.id, data)
            watchers = session.list_watchers()
            sent = 0
            for uid in watchers:
                try:
                    await bot.send_message(uid, f"Объявление цеха:\n{text}")
                    sent += 1
                except Exception as exc:  # noqa: BLE001 - рассылка не должна падать целиком
                    logger.warning("broadcast to %s failed: %s", uid, exc)
            await message.answer(f"Рассылка отправлена: {sent} из {len(watchers)}.")
            return

    return dp


async def main() -> None:
    setup_logging()
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    if not BOT_TOKEN or BOT_TOKEN.startswith("123456"):
        raise SystemExit("Укажите BOT_TOKEN в py_bot/.env (см. .env.example)")
    bot = Bot(token=BOT_TOKEN)
    dp = create_dispatcher()
    logger.info("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
