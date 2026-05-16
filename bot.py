import asyncio
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS
from keyboards import admin_panel_kb
import database as db

router = Router()
logger = logging.getLogger(__name__)


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


class BroadcastStates(StatesGroup):
    waiting_message = State()
    waiting_confirm = State()


# ── Subscribe / Unsubscribe ───────────────────────────────

@router.message(F.text == "🔔 Подписаться на рассылку")
async def subscribe(message: Message):
    added = db.add_subscriber(message.chat.id)
    if added:
        await message.answer(
            "✅ Ты подписан на рассылку!\n"
            "Теперь ты будешь получать важные сообщения от администратора."
        )
    else:
        await message.answer("ℹ️ Ты уже подписан на рассылку.")


@router.message(F.text == "🔕 Отписаться от рассылки")
async def unsubscribe(message: Message):
    removed = db.remove_subscriber(message.chat.id)
    if removed:
        await message.answer("✅ Ты отписан от рассылки.")
    else:
        await message.answer("ℹ️ Ты не был подписан на рассылку.")


# ── Broadcast (admin) ─────────────────────────────────────

@router.message(F.text == "📨 Рассылка")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    count = db.subscriber_count()
    await message.answer(
        f"📨 <b>Рассылка</b>\n\n"
        f"Сейчас <b>{count}</b> подписчиков.\n\n"
        f"Отправь сообщение для рассылки (текст, фото или документ).\n"
        f"Напиши /cancel для отмены.",
        parse_mode="HTML"
    )
    await state.set_state(BroadcastStates.waiting_message)


@router.message(BroadcastStates.waiting_message, F.text == "/cancel")
async def broadcast_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Рассылка отменена.", reply_markup=admin_panel_kb())


@router.message(BroadcastStates.waiting_message)
async def broadcast_got_message(message: Message, state: FSMContext):
    # Save message info for forwarding
    msg_data = {
        "message_id": message.message_id,
        "chat_id": message.chat.id,
        "type": "text",
    }

    if message.photo:
        msg_data["type"] = "photo"
        msg_data["file_id"] = message.photo[-1].file_id
        msg_data["caption"] = message.caption or ""
    elif message.document:
        msg_data["type"] = "document"
        msg_data["file_id"] = message.document.file_id
        msg_data["caption"] = message.caption or ""
    elif message.text:
        msg_data["type"] = "text"
        msg_data["text"] = message.text
    else:
        await message.answer("⚠️ Поддерживаются только текст, фото и документы.")
        return

    await state.update_data(msg_data=msg_data)

    count = db.subscriber_count()
    await message.answer(
        f"👀 Проверь сообщение выше.\n\n"
        f"Отправить его <b>{count}</b> подписчикам?\n\n"
        f"Напиши <b>да</b> для отправки или <b>нет</b> для отмены.",
        parse_mode="HTML"
    )
    await state.set_state(BroadcastStates.waiting_confirm)


@router.message(BroadcastStates.waiting_confirm, F.text.lower().in_({"нет", "no", "cancel", "/cancel"}))
async def broadcast_no(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Рассылка отменена.", reply_markup=admin_panel_kb())


@router.message(BroadcastStates.waiting_confirm, F.text.lower().in_({"да", "yes", "да!"}))
async def broadcast_yes(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    msg_data = data["msg_data"]
    await state.clear()

    subscribers = db.get_subscribers()
    if not subscribers:
        await message.answer("ℹ️ Нет подписчиков для рассылки.")
        return

    status_msg = await message.answer(f"⏳ Отправляю рассылку {len(subscribers)} подписчикам...")

    sent = 0
    failed = 0

    for chat_id in subscribers:
        try:
            if msg_data["type"] == "text":
                await bot.send_message(chat_id, msg_data["text"])
            elif msg_data["type"] == "photo":
                await bot.send_photo(chat_id, msg_data["file_id"],
                                     caption=msg_data.get("caption"))
            elif msg_data["type"] == "document":
                await bot.send_document(chat_id, msg_data["file_id"],
                                        caption=msg_data.get("caption"))
            sent += 1
            await asyncio.sleep(0.05)  # Rate limiting
        except Exception as e:
            logger.warning(f"Failed to send to {chat_id}: {e}")
            failed += 1

    await status_msg.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📤 Отправлено: {sent}\n"
        f"❌ Не доставлено: {failed}",
        parse_mode="HTML"
    )
    await message.answer("Готово!", reply_markup=admin_panel_kb())


@router.message(BroadcastStates.waiting_confirm)
async def broadcast_confirm_unclear(message: Message):
    await message.answer("Напиши <b>да</b> или <b>нет</b>.", parse_mode="HTML")
