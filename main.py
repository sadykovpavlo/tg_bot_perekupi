from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, StateFilter, Text
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message, PhotoSize)

BOT_TOKEN = '6151759366:AAFOh5WJsy3x5kKyWj-XegNmjKlhf8a3Wh0'

# Инициализируем хранилище (создаем экземпляр класса MemoryStorage)
storage: MemoryStorage = MemoryStorage()

# Создаем объекты бота и диспетчера
bot: Bot = Bot(BOT_TOKEN)
dp: Dispatcher = Dispatcher(storage=storage)

# Создаем "базу данных" пользователей
user_dict: dict[int, dict[str, str | int | bool]] = {}


# Cоздаем класс, наследуемый от StatesGroup, для группы состояний нашей FSM
class FSMFillCarInfo(StatesGroup):
    # Создаем экземпляры класса State, последовательно
    # перечисляя возможные состояния, в которых будет находиться
    # бот в разные моменты взаимодейтсвия с пользователем
    fill_model = State()  # Состояние ожидание ввода марки авто
    fill_year_of_build = State()  # Состояние ожидания ввода года выпуска авто
    fill_engine_type = State()  # Состояние ввода типа двигателя
    fill_capacity = State()  # Состояние ввода обьема или можности
    fill_gear_box_type = State()  # Состояние ожидания ввода типа коробки
    fill_if_has_crash = State()  # Состояние ожидания выбора были ли ДТП
    upload_photo = State()  # Состояние ожидания загрузки фото
    upload_photo_of_crash_datal = State()  # Состояние загрузки фото аварии
    fill_price = State()  # Состояние ожидания заполнение цены на авто


@dp.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):
    await message.answer(text='Привіт я Бот Перекуп\n\n'
                              'Заповніть форму для продажі авто - '
                              'відправте команду /fillform')


# Этот хэндлер будет срабатывать на команду "/cancel" в любых состояниях,
# кроме состояния по умолчанию, и отключать машину состояний
@dp.message(Command(commands='cancel'), ~StateFilter(default_state))
async def process_cancel_command_state(message: Message, state: FSMContext):
    await message.answer(text='Вы вышли из машины состояний\n\n'
                              'Чтобы снова перейти к заполнению анкеты - '
                              'отправьте команду /fillform')
    # Сбрасываем состояние
    await state.clear()


# Этот хэндлер будет срабатывать на команду "/cancel" в состоянии
# по умолчанию и сообщать, что эта команда доступна в машине состояний
@dp.message(Command(commands='cancel'), StateFilter(default_state))
async def process_cancel_command(message: Message):
    await message.answer(text='Отменять нечего. Вы вне машины состояний\n\n'
                              'Чтобы перейти к заполнению анкеты - '
                              'отправьте команду /fillform')


# Этот хэндлер будет срабатывать на команду /fillform
# и переводить бота в состояние ожидания ввода имени
@dp.message(Command(commands='fillform'), StateFilter(default_state))
async def process_fillform_command(message: Message, state: FSMContext):
    await message.answer(text='Напишіть марку та модель аввто одним повідомленням')
    # Устанавливаем состояние ожидания ввода имени
    await state.set_state(FSMFillCarInfo.fill_model)


# Этот хэндлер будет срабатывать, если введено корректное имя
# и переводить в состояние ожидания ввода возраста

@dp.message(StateFilter(FSMFillCarInfo.fill_model), lambda massage: len(massage.text) >= 4)
async def process_name_sent(message: Message, state: FSMContext):
    # Cохраняем введенное имя в хранилище по ключу "model"
    await state.update_data(model=message.text,
                            user_url=message.from_user.url,
                            user_name=message.from_user.full_name)
    await message.answer(text='Дякую!\n\nнапишіть рік випуску авто')

    # Устанавливаем состояние ожидания ввода возраста
    await state.set_state(FSMFillCarInfo.fill_year_of_build)
    # Процесс добавления года віпуска авто


@dp.message(StateFilter(FSMFillCarInfo.fill_year_of_build), F.text)
async def process_year_of_build_sent(message: Message, state: FSMContext):
    await state.update_data(year_of_build=message.text)
    await message.answer(text='Дякую!\n\nНапишіть тип палива двигуна\n'
                              'Або елеткро чи гібрит')
    await state.set_state(FSMFillCarInfo.fill_engine_type)


# Этот хэндлер будет срабатывать, если во время ввода имени
# будет введено что-то некорректное
@dp.message(StateFilter(FSMFillCarInfo.fill_model))
async def warning_not_name(message: Message):
    await message.answer(text='Те що ви відправили не схоже на марку та модель авто\n\n'
                              'Спробуйте ще раз\n\n'
                              'Мінімальна кількість символів - 4\n\n'
                              'Для відміни відправки форми - '
                              'відправте команду /cancel')


@dp.message(StateFilter(FSMFillCarInfo.fill_engine_type), F.text)
async def process_engine_type_sent(message: Message, state: FSMContext):
    await state.update_data(engine_type=message.text)
    await message.answer(text='Дякую! Тепер напишить обʼєм двигуна / для електро кількіть кВт')
    await state.set_state(FSMFillCarInfo.fill_capacity)


@dp.message(StateFilter(FSMFillCarInfo.fill_capacity), F.text)
async def process_of_add_capacity(message: Message, state: FSMContext):
    await state.update_data(engine_capacity=message.text)
    # buttons
    await message.answer(text='Напишіть тип коробки передач')
    await state.set_state(FSMFillCarInfo.fill_gear_box_type)


# Этот хэндлер будет срабатывать на нажатие кнопки при
# выборе пола и переводить в состояние отправки фото
@dp.message(StateFilter(FSMFillCarInfo.fill_gear_box_type))
async def process_fill_gear_box_type(message: Message, state: FSMContext):
    await state.update_data(gear_box=message.text)
    yes_button = InlineKeyboardButton(text='Yes',
                                      callback_data='yes')
    no_button = InlineKeyboardButton(text='No',
                                     callback_data='no')
    keyboard: list[list[InlineKeyboardButton]] = [[yes_button, no_button]]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(text='Чи була авто в ДТП?',
                         reply_markup=markup)
    await state.set_state(FSMFillCarInfo.fill_if_has_crash)


# # Этот хэндлер будет срабатывать на нажатие кнопки при
# # выборе пола и переводить в состояние отправки фото
@dp.callback_query(StateFilter(FSMFillCarInfo.fill_if_has_crash),
                   Text(text=['yes', 'no']))
async def process_gender_press(callback: CallbackQuery, state: FSMContext):
    # Cохраняем пол (callback.data нажатой кнопки) в хранилище,
    # по ключу "gender"
    await state.update_data(crash=callback.data)
    # Удаляем сообщение с кнопками, потому что следующий этап - загрузка фото
    # чтобы у пользователя не было желания тыкать кнопки
    await callback.message.delete()
    await callback.message.answer(text='Додайте фото')
    # # Устанавливаем состояние ожидания загрузки фото
    await state.set_state(FSMFillCarInfo.upload_photo)


# Этот хэндлер будет срабатывать, если отправлено фото
# и переводить в состояние выбора образования
@dp.message(StateFilter(FSMFillCarInfo.upload_photo),
            F.photo[-1].as_('largest_photo'))
async def process_photo_sent(message: Message,
                             state: FSMContext,
                             largest_photo: PhotoSize):
    # Cохраняем данные фото (file_unique_id и file_id) в хранилище
    # по ключам "photo_unique_id" и "photo_id"
    await state.update_data(photo_unique_id=largest_photo.file_unique_id,
                            photo_id=largest_photo.file_id)
    await message.answer(text='Дякую!\n\nВкажіть ціну')
    await state.set_state(FSMFillCarInfo.fill_price)


@dp.message(StateFilter(FSMFillCarInfo.fill_price))
async def process_fill_price(message: Message,
                             state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer(text='Дякую. Менеджер звʼяжеться з вами')
    user_dict[message.from_user.id] = await state.get_data()
    await state.clear()
    await bot.send_photo(chat_id='-1001717002913',
                         photo=f'{user_dict[message.from_user.id]["photo_id"]}',
                         caption=f'Імʼя: {user_dict[message.from_user.id]["user_name"]}\n'
                                 f'Імʼя: {user_dict[message.from_user.id]["user_url"]}\n'
                                 f'Авто: {user_dict[message.from_user.id]["model"]}\n'
                                 f'Двигун(Тип/Паливо): {user_dict[message.from_user.id]["engine_type"]}\n'
                                 f'Обʼєм: {user_dict[message.from_user.id]["engine_capacity"]}\n'
                                 f'Коробка: {user_dict[message.from_user.id]["gear_box"]}\n'
                                 f'Рік: {user_dict[message.from_user.id]["year_of_build"]}\n'
                                 f'ДТП: {user_dict[message.from_user.id]["crash"]}\n'
                                 f'Ціна: {user_dict[message.from_user.id]["price"]}')


# Запускаем поллинг
if __name__ == '__main__':
    dp.run_polling(bot)
