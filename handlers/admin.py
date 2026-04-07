from aiogram import Router, Bot, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message


router = Router()


@router.message(F.is_topic_message, ~Command("close"))
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


@router.message(Command("close"), F.is_topic_message)
async def close_topic(message: Message, state: FSMContext, bot: Bot):
    """Закриття діалогу та очищення зв'язків у Redis"""
    topic_id = message.message_thread_id
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
            
        await message.answer("✅ Діалог закрито. Зв'язок з клієнтом розірвано.")
        
        # Опціонально: можна закрити топік в Telegram
        try:
            await bot.close_forum_topic(chat_id=message.chat.id, message_thread_id=topic_id)
        except Exception as e:
            await message.answer(f"Примітка: не вдалося закрити топік засобами Telegram: {e}")
    else:
        await message.answer("Цей топік не має активного зв'язку з клієнтом.")