from aiogram import Router, Bot, F
import logging
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)



router: Router = Router()


@router.message(F.chat.type == 'private', StateFilter(default_state), ~Command(commands=['help', 'fillform', 'cancel']), ~CommandStart())
async def answer_for_any_message(message: Message, bot: Bot, state: FSMContext, chat_id: str):
    user_id = message.from_user.id
    redis = state.storage.redis
    
    # 1. Шукаємо нову систему (Топіки)
    topic_id_bytes = await redis.get(f"user:{user_id}:topic")
    if topic_id_bytes:
        topic_id = int(topic_id_bytes)
        client_name = message.from_user.full_name
        from_text = f"👤 Від: {client_name}"

        if message.text:
            await bot.send_message(
                chat_id=chat_id,
                text=f"{from_text}\n\n{message.text}",
                message_thread_id=topic_id
            )
        else:
            try:
                # Копіюємо медіа (фото, відео і т.д.) в топік
                await message.copy_to(
                    chat_id=chat_id,
                    message_thread_id=topic_id,
                    caption=f"{from_text}\n\n{message.caption or ''}".strip()
                )
            except Exception:
                # Fallback для типів без caption
                await bot.send_message(
                    chat_id=chat_id,
                    text=from_text,
                    message_thread_id=topic_id
                )
                await message.copy_to(chat_id=chat_id, message_thread_id=topic_id)
    else:
        # TODO: LEGACY - Видалити блок перевірки активного чату після міграції
        # ПЕРЕВІРКА ЛЕГАСІ-ЧАТУ (Приватний чат з менеджером)
        manager_id_bytes = await redis.get(f"active_chat:{user_id}")
        if manager_id_bytes:
            manager_id = int(manager_id_bytes)
            client_name = message.from_user.full_name
            from_text = f"👤 [Legacy] Від: {client_name}"
            
            try:
                if message.text:
                    await bot.send_message(chat_id=manager_id, text=f"{from_text}\n\n{message.text}")
                else:
                    await message.copy_to(chat_id=manager_id, caption=f"{from_text}\n\n{message.caption or ''}".strip())
                return
            except Exception as e:
                logging.error(f"Failed to relay to legacy manager {manager_id}: {e}")

        await message.answer(text='Привіт!\n\n'
                                  'Щоб продати своє авто - '
                                  'натисніть -> /fillform')


@router.message(F.chat.type == 'private', CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):
    start_button = InlineKeyboardButton(text='Хочу продати авто  🚗',
                                        callback_data='fillform')
    keyboard: list[list[InlineKeyboardButton]] = [[start_button]]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(text='Привіт! Якщо хочеш продати авто натисніть на кнопку ⬇️',
                         reply_markup=markup)


# Этот хэндлер будет срабатывать на команду "/cancel" в любых состояниях,
# кроме состояния по умолчанию, и отключать машину состояний
@router.message(Command(commands='cancel'), ~StateFilter(default_state))
async def process_cancel_command_state(message: Message, state: FSMContext):
    await message.answer(text='Ви перервали заповнення форми\n\n'
                              'Для того щоб почати заново - '
                              'натисніть -> /fillform')
    # Сбрасываем состояние
    await state.clear()


# Этот хэндлер будет срабатывать на команду "/cancel" в состоянии
# по умолчанию и сообщать, что эта команда доступна в машине состояний
@router.message(Command(commands='cancel'), StateFilter(default_state))
async def process_cancel_command(message: Message):
    await message.answer(text='Ви ще не почали заповнювати форму.\n\n'
                              'Щоб почати - '
                              'натисніть -> /fillform')


@router.message(Command(commands='help'))
async def process_of_help(message: Message):
    await message.answer(text='Щоб почати - '
                              'натисніть -> /fillform\n'
                              'Щоб перевати заповнення форми - натисніть -> /cancel ')


@router.message(F.chat.type == 'private', Command(commands='fillform'), StateFilter(default_state))
async def fillform_comand_message(message: Message):
    start_button = InlineKeyboardButton(text='Хочу продати авто  🚗',
                                        callback_data='fillform')
    keyboard: list[list[InlineKeyboardButton]] = [[start_button]]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(text='Привіт! Якщо хочеш продати авто нажимай на кнопку ⬇️',
                         reply_markup=markup)


@router.message(Command(commands='fillform'), ~StateFilter(default_state))
async def fillform_comand_message_not_def(message: Message):
    await message.answer(text='Ви вже почали заповнювати форму.\n'
                              'Щоб перевати заповнення форми - натисніть -> /cancel ')
