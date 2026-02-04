from aiogram import Router, Bot
from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.base import StorageKey
from aiogram.types import (
    CallbackQuery,
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

router = Router()

# This is a temporary in-memory storage.
# For production, consider using Redis or a database.
active_chats = {}  # {client_id: manager_id}


class AdminStates(StatesGroup):
    chatting = State()


@router.callback_query(Text(startswith="ans:"))
async def start_chat_with_user(callback: CallbackQuery, state: FSMContext, bot: Bot):
    target_user_id = int(callback.data.split(":")[1])
    manager_id = callback.from_user.id

    if target_user_id in active_chats and active_chats.get(target_user_id) != manager_id:
        await callback.answer("Інший менеджер вже спілкується з цим клієнтом.", show_alert=True)
        return
    
    if target_user_id in active_chats and active_chats.get(target_user_id) == manager_id:
        await callback.answer()
        return

    # Set state for manager in their private chat
    storage = state.storage
    manager_private_chat_key = StorageKey(bot_id=bot.id, user_id=manager_id, chat_id=manager_id)
    manager_fsm_context = FSMContext(bot=bot, storage=storage, key=manager_private_chat_key)
    await manager_fsm_context.set_state(AdminStates.chatting)
    await manager_fsm_context.set_data({'target_user_id': target_user_id})

    active_chats[target_user_id] = manager_id

    bot_info = await bot.get_me()
    
    go_to_chat_button = InlineKeyboardButton(
        text="↪️ Перейти в чат",
        url=f"https://t.me/{bot_info.username}"
    )

    original_button = InlineKeyboardButton(
        text="💬 Відповісти клієнту",
        callback_data=callback.data
    )

    end_chat_button = InlineKeyboardButton(
        text="❌ Завершити діалог",
        callback_data=f"end_chat:{target_user_id}"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[original_button], [go_to_chat_button], [end_chat_button]])

    await callback.message.edit_reply_markup(reply_markup=keyboard)

    # Client notification
    await bot.send_message(
        chat_id=target_user_id,
        text="Менеджер підключився до чату."
    )
    await callback.answer("Ви підключились до діалогу. Тепер перейдіть в чат з ботом і відправте повідомлення.", show_alert=True)


@router.message(StateFilter(AdminStates.chatting))
async def relay_message_to_client(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    if target_user_id:
        await bot.send_message(chat_id=target_user_id, text=message.text)


@router.callback_query(Text(startswith="end_chat:"))
async def end_chat_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    target_user_id = int(callback.data.split(":")[1])
    manager_id = callback.from_user.id # This is the manager who ends the chat

    # Clear state for manager in their private chat
    storage = state.storage
    manager_private_chat_key = StorageKey(bot_id=bot.id, user_id=manager_id, chat_id=manager_id)
    manager_fsm_context = FSMContext(bot=bot, storage=storage, key=manager_private_chat_key)
    await manager_fsm_context.clear()

    original_button = InlineKeyboardButton(
        text="💬 Відповісти клієнту",
        callback_data=f"ans:{target_user_id}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[original_button]])
    await callback.message.edit_reply_markup(reply_markup=keyboard)

    if target_user_id in active_chats:
        del active_chats[target_user_id]
    await bot.send_message(chat_id=target_user_id, text="Менеджер завершив діалог.")
    
    await callback.answer("Діалог завершено.")