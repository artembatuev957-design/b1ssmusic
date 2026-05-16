from aiogram import Router, F, Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS
from keyboards import admin_panel_kb
import database as db

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


class ScheduleStates(StatesGroup):
    waiting_file = State()


# ── View schedule ─────────────────────────────────────────

@router.message(F.text == "📅 Расписание")
async def view_schedule(message: Message, bot: Bot):
    info = db.get_schedule_info()
    if not info:
        await message.answer("📭 Расписание ещё не загружено. Обратись к учителю.")
        return

    caption = info.get("caption") or "📅 <b>Актуальное расписание</b>"
    caption += f"\n\n<i>Обновлено: {info['updated_at']}</i>"

    file_type = info.get("file_type", "document")
    file_id = info["file_id"]

    if file_type == "photo":
        await bot.send_photo(message.chat.id, file_id, caption=caption, parse_mode="HTML")
    elif file_type == "document":
        await bot.send_document(message.chat.id, file_id, caption=caption, parse_mode="HTML")
    else:
        await message.answer(caption, parse_mode="HTML")


# ── Upload schedule (admin) ───────────────────────────────

@router.message(F.text == "📤 Загрузить расписание")
async def upload_schedule_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "📤 Отправь фото или файл расписания.\n"
        "Можно добавить подпись к сообщению (она станет заголовком).\n\n"
        "Напиши /cancel для отмены."
    )
    await state.set_state(ScheduleStates.waiting_file)


@router.message(ScheduleStates.waiting_file, F.text == "/cancel")
async def upload_schedule_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено.", reply_markup=admin_panel_kb())


@router.message(ScheduleStates.waiting_file, F.photo)
async def upload_schedule_photo(message: Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    caption = message.caption or None
    db.set_schedule(file_id, "photo", caption)
    await state.clear()
    await message.answer("✅ Расписание (фото) успешно обновлено!", reply_markup=admin_panel_kb())


@router.message(ScheduleStates.waiting_file, F.document)
async def upload_schedule_document(message: Message, state: FSMContext):
    file_id = message.document.file_id
    caption = message.caption or None
    db.set_schedule(file_id, "document", caption)
    await state.clear()
    await message.answer("✅ Расписание (файл) успешно обновлено!", reply_markup=admin_panel_kb())


@router.message(ScheduleStates.waiting_file)
async def upload_schedule_wrong(message: Message):
    await message.answer("⚠️ Пожалуйста, отправь фото или файл (документ).")
