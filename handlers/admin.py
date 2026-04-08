from aiogram import Router, Bot, F
from aiogram.filters import Command, StateFilter, Text
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup



# TODO: LEGACY - Видалити AdminStates та legacy-хендлери після повної міграції на топіки
class AdminStates(StatesGroup):
    chatting = State()


router = Router()



async def _perform_close_topic(chat_id: int, topic_id: int, state: FSMContext, bot: Bot):
    """Внутрішня функція для закриття топіка"""
    redis = state.storage.redis
    user_id_bytes = await redis.get(f"topic:{topic_id}")
    
    if user_id_bytes:
        user_id = int(user_id_bytes)
        # Видаляємо зв'язки
        await redis.delete(f"topic:{topic_id}")
        await redis.delete(f"user:{user_id}:topic")
        
        # Сповіщаємо клієнта
        try:
            await bot.send_message(chat_id=user_id, text="Дякуємо! Менеджер завершив діалог.")
        except:
            pass
        
        # Закриваємо топік в Telegram
        try:
            await bot.close_forum_topic(chat_id=chat_id, message_thread_id=topic_id)
        except:
            pass
        return True
    return False

async def _perform_delete_topic(chat_id: int, topic_id: int, state: FSMContext, bot: Bot):
    """Внутрішня функція для видалення топіка"""
    redis = state.storage.redis
    user_id_bytes = await redis.get(f"topic:{topic_id}")
    
    if user_id_bytes:
        user_id = int(user_id_bytes)
        await redis.delete(f"topic:{topic_id}")
        await redis.delete(f"user:{user_id}:topic")
        
        try:
            await bot.send_message(chat_id=user_id, text="Дякуємо! Діалог завершено.")
        except:
            pass
            
    # Видаляємо топік в Telegram (це можна робити навіть якщо зв'язку в Redis вже немає)
    try:
        await bot.delete_forum_topic(chat_id=chat_id, message_thread_id=topic_id)
        return True
    except:
        return False

@router.message(F.is_topic_message, ~F.from_user.is_bot, ~Command("close"), ~Command("delete"))
async def relay_from_topic_to_client(message: Message, state: FSMContext, bot: Bot):
    """Пересилка повідомлення з топіка клієнту"""
    topic_id = message.message_thread_id
    redis = state.storage.redis
    
    user_id_bytes = await redis.get(f"topic:{topic_id}")
    if not user_id_bytes:
        return # Цей топік не пов'язаний з клієнтом через бота
    
    user_id = int(user_id_bytes)
    try:
        # Копіюємо повідомлення юзеру
        await message.copy_to(chat_id=user_id)
    except Exception as e:
        await message.answer(f"⚠️ Не вдалося відправити повідомлення клієнту: {e}")

@router.message(~F.is_topic_message, StateFilter(AdminStates.chatting))
async def legacy_relay_to_client(message: Message, state: FSMContext, bot: Bot):
    """TODO: LEGACY - Видалити після міграції"""
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    
    if not target_user_id:
        await message.answer("Помилка: клієнт не знайдений у легасі-чаті.")
        return

    try:
        await message.copy_to(chat_id=target_user_id)
    except Exception as e:
        await message.answer(f"⚠️ Не вдалося відправити повідомлення клієнту: {e}")


@router.message(Command("close"), F.is_topic_message)
async def close_topic_cmd(message: Message, state: FSMContext, bot: Bot):
    """Закриття діалогу через команду /close"""
    success = await _perform_close_topic(message.chat.id, message.message_thread_id, state, bot)
    if success:
        await message.answer("✅ Діалог закрито. Зв'язок з клієнтом розірвано.")
    else:
        await message.answer("Цей топік не має активного зв'язку з клієнтом або вже закритий.")

@router.message(Command("delete"), F.is_topic_message)
async def delete_topic_cmd(message: Message, state: FSMContext, bot: Bot):
    """Видалення топіка через команду /delete"""
    await message.answer("⏳ Видаляю топік...")
    await _perform_delete_topic(message.chat.id, message.message_thread_id, state, bot)

@router.callback_query(F.data.startswith("ans:"))
async def legacy_start_chat_with_user(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """TODO: LEGACY - Видалити після міграції"""
    target_user_id = int(callback.data.split(":")[1])
    manager_id = callback.from_user.id
    redis = state.storage.redis

    # Перевіряємо чи не зайнятий клієнт іншим менеджером (в легасі системі)
    active_manager_bytes = await redis.get(f"active_chat:{target_user_id}")
    if active_manager_bytes and int(active_manager_bytes) != manager_id:
        await callback.answer("Інший менеджер вже спілкується з цим клієнтом у приватному чаті.", show_alert=True)
        return

    # Встановлюємо стан менеджеру в його приватці
    from aiogram.fsm.storage.base import StorageKey
    manager_key = StorageKey(bot_id=bot.id, user_id=manager_id, chat_id=manager_id)
    manager_state = FSMContext(bot=bot, storage=state.storage, key=manager_key)
    
    await manager_state.set_state(AdminStates.chatting)
    await manager_state.set_data({'target_user_id': target_user_id})
    
    # Зберігаємо легасі-зв'язок у Redis
    await redis.set(f"active_chat:{target_user_id}", manager_id)
    
    await callback.answer("Ви підключились до легасі-діалогу (приватний чат).", show_alert=True)
    await bot.send_message(chat_id=target_user_id, text="Менеджер підключився до чату.")


@router.callback_query(F.data == "close_dialog")
async def close_dialog_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Обробка кнопки 'Закрити діалог'"""
    await callback.answer()
    success = await _perform_close_topic(callback.message.chat.id, callback.message.message_thread_id, state, bot)
    if success:
        await callback.message.answer("✅ Діалог закрито.")
    else:
        await callback.message.answer("⚠️ Помилка: діалог вже закрито або не знайдено.")

@router.callback_query(F.data == "delete_dialog")
async def delete_dialog_callback(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Обробка кнопки 'Видалити топік'"""
    await callback.answer("Видаляю топік...")
    await _perform_delete_topic(callback.message.chat.id, callback.message.message_thread_id, state, bot)