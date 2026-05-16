from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from config import SUBJECTS


def main_menu_kb(is_admin: bool = False) -> ReplyKeyboardMarkup:
    """Main menu keyboard."""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="📚 Домашнее задание"))
    builder.row(KeyboardButton(text="📅 Расписание"))
    builder.row(KeyboardButton(text="🔔 Подписаться на рассылку"))
    builder.row(KeyboardButton(text="🔕 Отписаться от рассылки"))
    if is_admin:
        builder.row(KeyboardButton(text="⚙️ Панель администратора"))
    return builder.as_markup(resize_keyboard=True)


def admin_panel_kb() -> ReplyKeyboardMarkup:
    """Admin panel keyboard."""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="✏️ Добавить ДЗ"))
    builder.row(KeyboardButton(text="🗑 Удалить ДЗ по предмету"))
    builder.row(KeyboardButton(text="🧹 Очистить всё ДЗ"))
    builder.row(KeyboardButton(text="📤 Загрузить расписание"))
    builder.row(KeyboardButton(text="📨 Рассылка"))
    builder.row(KeyboardButton(text="👥 Статистика"))
    builder.row(KeyboardButton(text="🏠 Главное меню"))
    return builder.as_markup(resize_keyboard=True)


def subjects_kb(callback_prefix: str) -> InlineKeyboardMarkup:
    """Subjects selection keyboard."""
    builder = InlineKeyboardBuilder()
    for subject in SUBJECTS:
        builder.button(
            text=subject,
            callback_data=f"{callback_prefix}:{subject}"
        )
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="cancel"))
    return builder.as_markup()


def confirm_kb(action: str) -> InlineKeyboardMarkup:
    """Confirm/cancel keyboard."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да", callback_data=f"confirm:{action}")
    builder.button(text="❌ Нет", callback_data="cancel")
    return builder.as_markup()


def homework_view_kb() -> InlineKeyboardMarkup:
    """Keyboard for viewing homework by subject."""
    builder = InlineKeyboardBuilder()
    for subject in SUBJECTS:
        builder.button(
            text=subject,
            callback_data=f"view_hw:{subject}"
        )
    builder.adjust(2)
    builder.row(InlineKeyboardButton(text="📋 Все предметы", callback_data="view_hw:all"))
    return builder.as_markup()


def remove_kb() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()
