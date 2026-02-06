from aiogram import Router, Bot
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from handlers.admin import active_chats

router: Router = Router()


@router.message(StateFilter(default_state), ~Command(commands=['help', 'fillform', 'cancel']), ~CommandStart())
async def answer_for_any_message(message: Message, bot: Bot):
    if message.from_user.id in active_chats:
        manager_id = active_chats[message.from_user.id]
        client_name = message.from_user.full_name
        from_text = f"Відправлено від: {client_name}"

        if message.text:
            await bot.send_message(
                chat_id=manager_id,
                text=f"{from_text}\n\n{message.text}"
            )
        else:
            try:
                # Try to add caption. This works for photos, videos, documents.
                await message.copy_to(
                    chat_id=manager_id,
                    caption=f"{from_text}\n\n{message.caption or ''}".strip()
                )
            except TypeError:
                # Fallback for message types that don't support captions (e.g., stickers)
                await bot.send_message(
                    chat_id=manager_id,
                    text=from_text
                )
                await message.copy_to(chat_id=manager_id)
    else:
        await message.answer(text='Привіт!\n\n'
                                  'Щоб продати своє авто - '
                                  'натисніть -> /fillform')


@router.message(CommandStart(), StateFilter(default_state))
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


@router.message(Command(commands='fillform'), StateFilter(default_state))
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
