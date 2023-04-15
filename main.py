from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart, StateFilter, Text, BaseFilter
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (Message, KeyboardButton, ReplyKeyboardMarkup,
                           ReplyKeyboardRemove)
from aiogram.types import InputMediaPhoto

BOT_TOKEN = '6151759366:AAGNtavvreXK7eAxhNUth3Wpl0izf_UQghM'

# Инициализируем хранилище (создаем экземпляр класса MemoryStorage)
storage: MemoryStorage = MemoryStorage()

# Создаем объекты бота и диспетчера
bot: Bot = Bot(BOT_TOKEN)
dp: Dispatcher = Dispatcher(storage=storage)

# Создаем "базу данных" пользователей
user_dict: dict[int, dict[str, str | int | bool]] = {}


class PhotoFilter(BaseFilter):

    async def __call__(self, message: Message, state: FSMContext):
        user_dict[message.from_user.id] = await state.get_data()
        if user_dict[message.from_user.id]["photo"]:
            if len(user_dict[message.from_user.id]["photo"]) >= 4:
                return True
            else:
                return False
        else:
            return False


class MediaGroupFilter(BaseFilter):
    async def __call__(self, massage: Message):
        if massage.media_group_id:
            return True

        # Cоздаем класс, наследуемый от StatesGroup, для группы состояний нашей FSM


class FSMFillCarInfo(StatesGroup):
    fill_model = State()  # Состояние ожидание ввода марки авто
    fill_year_of_build = State()  # Состояние ожидания ввода года выпуска авто
    fill_engine_type = State()  # Состояние ввода типа двигателя
    fill_capacity = State()  # Состояние ввода обьема или можности
    fill_gear_box_type = State()  # Состояние ожидания ввода типа коробки
    fill_vin_or_numbers = State()  # Состояние ожидания выбора были ли ДТП
    upload_photo = State()  # Состояние ожидания загрузки фото
    fill_some_info = State()
    fill_contact_info = State()  # That state activate if user doesnt have user_name
    fill_price = State()  # Состояние ожидания заполнение цены на авто


@dp.message(StateFilter(default_state), ~Command(commands=['help', 'fillform', 'cancel']), ~CommandStart())
async def answer_for_any_message(message: Message):
    await message.answer(text='Привіт я Бот Перекуп\n\n'
                              'Заповніть форму для продажі авто - '
                              'натисніть -> /fillform')


@dp.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):
    await message.answer(text='Привіт я Бот Перекуп\n\n'
                              'Заповніть форму для продажі авто - '
                              'натисніть -> /fillform')


# Этот хэндлер будет срабатывать на команду "/cancel" в любых состояниях,
# кроме состояния по умолчанию, и отключать машину состояний
@dp.message(Command(commands='cancel'), ~StateFilter(default_state))
async def process_cancel_command_state(message: Message, state: FSMContext):
    await message.answer(text='Ви перервали заповнення форми\n\n'
                              'Для того щоб почати заново - '
                              'натисніть -> /fillform')
    # Сбрасываем состояние
    await state.clear()


# Этот хэндлер будет срабатывать на команду "/cancel" в состоянии
# по умолчанию и сообщать, что эта команда доступна в машине состояний
@dp.message(Command(commands='cancel'), StateFilter(default_state))
async def process_cancel_command(message: Message):
    await message.answer(text='Ви ще не почали заповнювати форму.\n\n'
                              'Щоб почати - '
                              'натисніть -> /fillform')


@dp.message(Command(commands='help'))
async def process_of_help(message: Message):
    await message.answer(text='Щоб почати - '
                              'натисніть -> /fillform\n'
                              'Щоб перевати заповнення форми - натисніть -> /cancel ')


# Этот хэндлер будет срабатывать на команду /fillform
# и переводить бота в состояние ожидания ввода марки и модели авто
@dp.message(Command(commands='fillform'), StateFilter(default_state))
async def process_fillform_command(message: Message, state: FSMContext):
    await message.answer(text='Напишіть марку та модель авто одним повідомленням')
    await state.set_state(FSMFillCarInfo.fill_model)


# Этот хэндлер будет срабатывать, если введено корректное марка и модель
# и переводить в состояние ожидания ввода года випуска авто

@dp.message(StateFilter(FSMFillCarInfo.fill_model), lambda massage: len(massage.text) >= 4, ~Text(text='/fillform'))
async def process_name_sent(message: Message, state: FSMContext):
    # Cохраняем введенное имя в хранилище по ключу "model"
    await state.update_data(model=message.text,
                            user_url=message.from_user.username,
                            user_name=message.from_user.full_name)
    await message.answer(text='Дякую!\n\nнапишіть рік випуску авто')

    await state.set_state(FSMFillCarInfo.fill_year_of_build)


@dp.message(StateFilter(FSMFillCarInfo.fill_year_of_build), F.text)
async def process_year_of_build_sent(message: Message, state: FSMContext):
    await state.update_data(year_of_build=message.text)
    await message.answer(text='Напишіть тип палива двигуна\n'
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


# that handler will work if add correct type of gearbox
@dp.message(StateFilter(FSMFillCarInfo.fill_gear_box_type))
async def process_fill_gear_box_type(message: Message, state: FSMContext):
    await state.update_data(gear_box=message.text)
    await message.answer(text='Напишіть VIN або державний номер авто: ', )
    await state.set_state(FSMFillCarInfo.fill_vin_or_numbers)


# That will star if correct ansfer for gearbox
@dp.message(StateFilter(FSMFillCarInfo.fill_vin_or_numbers), lambda massage: len(massage.text) >= 5)
async def process_vin_or_number(message: Message, state: FSMContext):
    await state.update_data(vin_or_num=message.text)
    await message.answer(text='Додайте від 4 до 10 фото')
    await state.set_state(FSMFillCarInfo.upload_photo)


@dp.message(StateFilter(FSMFillCarInfo.fill_vin_or_numbers))
async def incorrect_num_or_vin(message: Message):
    await message.answer(text="Вибачте, це не схоже на номер чи VIN\n"
                              "Спробуйте ще раз")


# Прцесс добаления фото/ сейчас есть бага если добалять все фото разом то у нас много сообщений о том что добавь фото
# добавить вопрос хочет ли еще фото юзер
@dp.message(StateFilter(FSMFillCarInfo.upload_photo),
            F.photo[-1].as_('largest_photo'))
async def process_photo_sent(message: Message,
                             state: FSMContext,
                             ):
    data = await state.get_data()
    if 'photos' in data:
        data['photos'].append(message.photo[-1].file_id)
    if 'photos' not in data:
        await state.update_data(photos=[])
        data = await state.get_data()
        data['photos'].append(message.photo[-1].file_id)
    if len(data['photos']) < 4:
        await state.update_data(photos=data["photos"])

    elif len(data['photos']) < 11:
        await state.update_data(photos=data["photos"])
        button_stop: KeyboardButton = KeyboardButton(text='Більше не додавати')
        keyboard: ReplyKeyboardMarkup = ReplyKeyboardMarkup(
            keyboard=[[button_stop]], resize_keyboard=True)
        await message.answer(reply_markup=keyboard, text='Ви можете додати ще фото')

    elif len(data['photos']) >= 10:
        await message.answer(text="Ви додали максимальну кількість фото!", reply_markup=ReplyKeyboardRemove())
        await message.answer(text='Напишіть декілька слів про ваше авто(підкраси, стан кузову, технічний стан,'
                                  ' комплектація, пробіг)')
        await state.set_state(FSMFillCarInfo.fill_some_info)


@dp.message(StateFilter(FSMFillCarInfo.upload_photo),
            Text(text='Більше не додавати'))
async def process_of_change_state_to_fill_price(message: Message, state: FSMContext):
    await message.answer(text="Напишіть декілька слів про ваше авто"
                              "(підкраси, стан кузову, технічний стан, комплектація, пробіг)",
                         reply_markup=ReplyKeyboardRemove())
    await state.set_state(FSMFillCarInfo.fill_some_info)


@dp.message(StateFilter(FSMFillCarInfo.upload_photo))
async def error_upload_photo(message: Message):
    await message.answer(text="Це не схоже на фото.\n"
                              "Додойте від 4 до 10 фото")


@dp.message(StateFilter(FSMFillCarInfo.fill_some_info), F.text)
async def process_adding_some_info(message: Message, state: FSMContext):
    await state.update_data(car_info=message.text)
    await message.answer(text='Вкажіть ціну: ')
    await state.set_state(FSMFillCarInfo.fill_price)


@dp.message(StateFilter(FSMFillCarInfo.fill_some_info))
async def error_info_filling(message: Message):
    await message.answer(text="Напишіть декілька слів про ваше авто(підкраси, стан кузову, технічний стан, "
                              "комплектація, пробіг):")


@dp.message(StateFilter(FSMFillCarInfo.fill_price), F.text)
async def process_fill_price(message: Message,
                             state: FSMContext):
    await state.update_data(price=message.text)
    user_dict[message.from_user.id] = await state.get_data()
    if user_dict[message.from_user.id]["user_url"]:
        await message.answer(text='Дякую. Менеджер звʼяжеться з вами')
        await state.clear()
        caption = f'Імʼя: {user_dict[message.from_user.id]["user_name"]}\nКонтакт: @{user_dict[message.from_user.id]["user_url"]}\nАвто: {user_dict[message.from_user.id]["model"]}\nДвигун(Тип/Паливо): {user_dict[message.from_user.id]["engine_type"]}\nОбʼєм: {user_dict[message.from_user.id]["engine_capacity"]}\nКоробка: {user_dict[message.from_user.id]["gear_box"]}\nРік: {user_dict[message.from_user.id]["year_of_build"]}\nVIN/Номер: {user_dict[message.from_user.id]["vin_or_num"]}\nЦіна: {user_dict[message.from_user.id]["price"]}\nПро авто: {user_dict[message.from_user.id]["car_info"]}'
        media: list = []
        photo_media = InputMediaPhoto(media=user_dict[message.from_user.id]["photos"][0], caption=caption)
        media.append(photo_media)
        object_photos = user_dict[message.from_user.id]["photos"][1:9]
        for object_photo in object_photos:
            photo_media = InputMediaPhoto(media=object_photo)
            media.append(photo_media)

        await bot.send_media_group(chat_id='-1001717002913', media=media)
        media = []
    else:
        await message.answer(text='Вкажіть Контактний номер')
        await state.set_state(FSMFillCarInfo.fill_contact_info)


@dp.message(StateFilter(FSMFillCarInfo.fill_price))
async def error_for_price(message: Message):
    await message.answer(text="Вкажіть ціну: ")


# This handler works if user doesn`t have user_name and added valid number
@dp.message(StateFilter(FSMFillCarInfo.fill_contact_info), F.text,
            lambda x: x.text.isdigit() and 10 <= len(x.text) <= 12)
async def process_add_contact(message: Message, state: FSMContext):
    await state.update_data(contact=message.text)
    user_dict[message.from_user.id] = await state.get_data()
    await message.answer(text='Дякую. Менеджер звʼяжеться з вами')
    await state.clear()
    caption = f'Імʼя: {user_dict[message.from_user.id]["user_name"]}\nКонтакт: {user_dict[message.from_user.id]["user_url"]}\nАвто: {user_dict[message.from_user.id]["model"]}\nДвигун(Тип/Паливо): {user_dict[message.from_user.id]["engine_type"]}\nОбʼєм: {user_dict[message.from_user.id]["engine_capacity"]}\nКоробка: {user_dict[message.from_user.id]["gear_box"]}\nРік: {user_dict[message.from_user.id]["year_of_build"]}\nVIN/Номер: {user_dict[message.from_user.id]["vin_or_num"]}\nЦіна: {user_dict[message.from_user.id]["price"]}\nПро авто: {user_dict[message.from_user.id]["car_info"]}'
    media: list = []
    photo_media = InputMediaPhoto(media=user_dict[message.from_user.id]["photos"][0], caption=caption)
    media.append(photo_media)
    object_photos = user_dict[message.from_user.id]["photos"][1:9]
    for object_photo in object_photos:
        photo_media = InputMediaPhoto(media=object_photo)
        media.append(photo_media)

    await bot.send_media_group(chat_id='-1001717002913', media=media)
    media = []


# Handler works when user sent not valid number
@dp.message(StateFilter(FSMFillCarInfo.fill_contact_info))
async def invalid_number(message: Message):
    await message.answer(text="Схоже Ви ввели не коректний номер.\n"
                              "Номер має складати від 10 до 12 символів\n"
                              "Спробуйте ще раз\n"
                              "Якщо ви вводили пчинаючи з ʼ+ʼ, приберіть ʼ+ʼ")


# Запускаем поллинг
if __name__ == '__main__':
    dp.run_polling(bot)
