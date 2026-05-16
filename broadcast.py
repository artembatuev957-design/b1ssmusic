from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS
from keyboards import main_menu_kb, admin_panel_kb
import database as db

router = Router()


class AdminStates(StatesGroup):
    waiting_confirm_clear_all = State()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


# ── /start ────────────────────────────────────────────────

@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    admin = is_admin(message.from_user.id)
    name = message.from_user.first_name or "ученик"

    text = (
        f"👋 Привет, <b>{name}</b>!\n\n"
        f"Я школьный бот. Здесь ты можешь:\n"
        f"📚 Смотреть домашние задания\n"
        f"📅 Просматривать расписание\n"
        f"🔔 Подписаться на рассылку новостей\n"
    )
    if admin:
        text += "\n⚙️ <b>Ты администратор</b> — доступна панель управления"

    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb(admin))


# ── /help ─────────────────────────────────────────────────

@router.message(Command("help"))
async def cmd_help(message: Message):
    admin = is_admin(message.from_user.id)
    text = (
        "ℹ️ <b>Помощь</b>\n\n"
        "<b>Для учеников:</b>\n"
        "• 📚 Домашнее задание — посмотреть ДЗ по предметам\n"
        "• 📅 Расписание — актуальное расписание\n"
        "• 🔔 Подписаться — получать рассылки\n"
        "• 🔕 Отписаться — отключить рассылки\n"
    )
    if admin:
        text += (
            "\n<b>Для администратора:</b>\n"
            "• ✏️ Добавить ДЗ — внести домашнее задание\n"
            "• 🗑 Удалить ДЗ — удалить по предмету\n"
            "• 🧹 Очистить всё ДЗ — сброс всех заданий\n"
            "• 📤 Загрузить расписание — обновить расписание\n"
            "• 📨 Рассылка — отправить сообщение всем подписчикам\n"
            "• 👥 Статистика — количество подписчиков\n"
        )
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu_kb(admin))


# ── Admin panel ───────────────────────────────────────────

@router.message(F.text == "⚙️ Панель администратора")
async def admin_panel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У тебя нет доступа к этой функции.")
        return
    await state.clear()
    await message.answer("⚙️ <b>Панель администратора</b>\n\nВыбери действие:",
                         parse_mode="HTML", reply_markup=admin_panel_kb())


@router.message(F.text == "🏠 Главное меню")
async def go_home(message: Message, state: FSMContext):
    await state.clear()
    admin = is_admin(message.from_user.id)
    await message.answer("🏠 Главное меню", reply_markup=main_menu_kb(admin))


# ── Statistics ────────────────────────────────────────────

@router.message(F.text == "👥 Статистика")
async def stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    count = db.subscriber_count()
    hw = db.get_all_homework()
    await message.answer(
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Подписчиков: <b>{count}</b>\n"
        f"📚 Заполненных ДЗ: <b>{len(hw)}</b>",
        parse_mode="HTML"
    )


# ── Clear all homework ────────────────────────────────────

@router.message(F.text == "🧹 Очистить всё ДЗ")
async def clear_all_hw_confirm(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    from keyboards import confirm_kb
    await message.answer(
        "⚠️ Ты уверен, что хочешь удалить <b>всё домашнее задание</b>?",
        parse_mode="HTML",
        reply_markup=confirm_kb("clear_all_hw")
    )
    await state.set_state(AdminStates.waiting_confirm_clear_all)


@router.callback_query(F.data == "confirm:clear_all_hw")
async def clear_all_hw_do(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    db.clear_all_homework()
    await state.clear()
    await callback.message.edit_text("✅ Всё домашнее задание удалено.")


@router.callback_query(F.data == "cancel")
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Отменено.")
