from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS, SUBJECTS, SUBJECT_KEYS
from keyboards import subjects_kb, homework_view_kb, admin_panel_kb
import database as db

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


class HomeworkStates(StatesGroup):
    choosing_subject_add = State()
    entering_text = State()
    waiting_file = State()
    choosing_subject_delete = State()


# ── View homework (students) ──────────────────────────────

@router.message(F.text == "📚 Домашнее задание")
async def view_homework_menu(message: Message):
    await message.answer(
        "📚 <b>Домашнее задание</b>\n\nВыбери предмет:",
        parse_mode="HTML",
        reply_markup=homework_view_kb()
    )


@router.callback_query(F.data.startswith("view_hw:"))
async def view_homework(callback: CallbackQuery, bot: Bot):
    subject = callback.data.split(":", 1)[1]

    if subject == "all":
        all_hw = db.get_all_homework()
        if not all_hw:
            await callback.message.edit_text("📭 Домашнее задание пока не задано ни по одному предмету.")
            return

        # Build reverse map: key -> subject name
        key_to_name = {v: k for k, v in SUBJECT_KEYS.items()}
        text = "📚 <b>Все домашние задания:</b>\n\n"
        for key, hw in all_hw.items():
            name = key_to_name.get(key, key)
            text += f"<b>{name}</b>\n"
            text += f"{hw['text']}\n"
            text += f"<i>Обновлено: {hw['updated_at']}</i>\n\n"

        await callback.message.edit_text(text, parse_mode="HTML")
        return

    # Single subject
    subject_key = SUBJECT_KEYS.get(subject)
    if not subject_key:
        await callback.answer("Предмет не найден.", show_alert=True)
        return

    hw = db.get_homework(subject_key)
    if not hw:
        await callback.message.edit_text(
            f"📭 По предмету <b>{subject}</b> домашнее задание не задано.",
            parse_mode="HTML"
        )
        return

    text = (
        f"📚 <b>{subject}</b>\n\n"
        f"{hw['text']}\n\n"
        f"<i>Обновлено: {hw['updated_at']}</i>"
    )

    if hw.get("file_id"):
        file_type = hw.get("file_type", "document")
        await callback.message.delete()
        chat_id = callback.message.chat.id
        if file_type == "photo":
            await bot.send_photo(chat_id, hw["file_id"], caption=text, parse_mode="HTML")
        elif file_type == "document":
            await bot.send_document(chat_id, hw["file_id"], caption=text, parse_mode="HTML")
        else:
            await bot.send_message(chat_id, text, parse_mode="HTML")
    else:
        await callback.message.edit_text(text, parse_mode="HTML")


# ── Add homework (admin) ──────────────────────────────────

@router.message(F.text == "✏️ Добавить ДЗ")
async def add_hw_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "✏️ Выбери предмет для добавления ДЗ:",
        reply_markup=subjects_kb("add_hw")
    )
    await state.set_state(HomeworkStates.choosing_subject_add)


@router.callback_query(F.data.startswith("add_hw:"), HomeworkStates.choosing_subject_add)
async def add_hw_subject_chosen(callback: CallbackQuery, state: FSMContext):
    subject = callback.data.split(":", 1)[1]
    await state.update_data(subject=subject)
    await callback.message.edit_text(
        f"✏️ <b>{subject}</b>\n\n"
        f"Введи текст домашнего задания.\n"
        f"Можешь также прикрепить фото или файл после текста.\n\n"
        f"Напиши /skip если хочешь загрузить только файл без текста.",
        parse_mode="HTML"
    )
    await state.set_state(HomeworkStates.entering_text)


@router.message(HomeworkStates.entering_text, F.text)
async def add_hw_text(message: Message, state: FSMContext):
    text = message.text
    if text == "/skip":
        text = ""
    await state.update_data(hw_text=text)
    await message.answer(
        "📎 Теперь отправь файл (фото или документ) — или напиши /done чтобы сохранить без файла."
    )
    await state.set_state(HomeworkStates.waiting_file)


@router.message(HomeworkStates.waiting_file, F.text == "/done")
async def add_hw_no_file(message: Message, state: FSMContext):
    data = await state.get_data()
    subject = data["subject"]
    hw_text = data.get("hw_text", "")
    subject_key = SUBJECT_KEYS.get(subject)

    if not hw_text and not data.get("file_id"):
        await message.answer("⚠️ Нельзя сохранить пустое задание. Введи текст или загрузи файл.")
        return

    db.set_homework(subject_key, hw_text or "📎 Смотри прикреплённый файл")
    await state.clear()
    await message.answer(
        f"✅ Домашнее задание по <b>{subject}</b> сохранено!",
        parse_mode="HTML",
        reply_markup=admin_panel_kb()
    )


@router.message(HomeworkStates.waiting_file, F.photo)
async def add_hw_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    subject = data["subject"]
    hw_text = data.get("hw_text", "📎 Смотри прикреплённое фото")
    subject_key = SUBJECT_KEYS.get(subject)
    file_id = message.photo[-1].file_id

    db.set_homework(subject_key, hw_text, file_id=file_id, file_type="photo")
    await state.clear()
    await message.answer(
        f"✅ Домашнее задание по <b>{subject}</b> сохранено с фото!",
        parse_mode="HTML",
        reply_markup=admin_panel_kb()
    )


@router.message(HomeworkStates.waiting_file, F.document)
async def add_hw_document(message: Message, state: FSMContext):
    data = await state.get_data()
    subject = data["subject"]
    hw_text = data.get("hw_text", "📎 Смотри прикреплённый файл")
    subject_key = SUBJECT_KEYS.get(subject)
    file_id = message.document.file_id

    db.set_homework(subject_key, hw_text, file_id=file_id, file_type="document")
    await state.clear()
    await message.answer(
        f"✅ Домашнее задание по <b>{subject}</b> сохранено с файлом!",
        parse_mode="HTML",
        reply_markup=admin_panel_kb()
    )


# ── Delete homework (admin) ───────────────────────────────

@router.message(F.text == "🗑 Удалить ДЗ по предмету")
async def delete_hw_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer(
        "🗑 Выбери предмет для удаления ДЗ:",
        reply_markup=subjects_kb("del_hw")
    )
    await state.set_state(HomeworkStates.choosing_subject_delete)


@router.callback_query(F.data.startswith("del_hw:"), HomeworkStates.choosing_subject_delete)
async def delete_hw_do(callback: CallbackQuery, state: FSMContext):
    subject = callback.data.split(":", 1)[1]
    subject_key = SUBJECT_KEYS.get(subject)
    deleted = db.clear_homework(subject_key)
    await state.clear()
    if deleted:
        await callback.message.edit_text(f"✅ ДЗ по <b>{subject}</b> удалено.", parse_mode="HTML")
    else:
        await callback.message.edit_text(f"ℹ️ По <b>{subject}</b> не было задания.", parse_mode="HTML")
