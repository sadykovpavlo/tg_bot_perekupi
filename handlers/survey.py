from aiogram import Router, F, Bot
from aiogram.filters import StateFilter, Text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InputMediaPhoto,
    InputMediaVideo,
)

from states.car_info import FSMFillCarInfo

router: Router = Router()

user_dict: dict[int, dict[str, str | int | bool]] = {}


# Этот хэндлер будет срабатывать на команду /fillform
# и переводить бота в состояние ожидания ввода марки и модели авто
@router.callback_query(Text(text='fillform'), StateFilter(default_state))
async def process_fillform_command(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(text='Напишіть марку та модель авто одним повідомленням: ')
    await state.set_state(FSMFillCarInfo.fill_model)


# Этот хэндлер будет срабатывать на команду /fillform
# и переводить бота в состояние ожидания ввода марки и модели авто
@router.callback_query(Text(text='fillform'), ~StateFilter(default_state))
async def process_fillform_command_not_default(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(text="Ви вже почали заповнювати форму.\n"
                                       "Щоб перевати заповнення форми - натисніть -> /cancel ")


# Этот хэндлер будет срабатывать, если введено корректное марка и модель
# и переводить в состояние ожидания ввода года випуска авто
@router.message(StateFilter(FSMFillCarInfo.fill_model), lambda massage: len(massage.text) >= 4, ~Text(text=['/fillform',
                                                                                                        '/start']))
async def process_name_sent(message: Message, state: FSMContext):
    # Cохраняем введенное имя в хранилище по ключу "model"
    await state.update_data(model=message.text,
                            user_url=message.from_user.username,
                            user_name=message.from_user.full_name)
    await message.answer(text='Напишіть назву міста, або населеного пункту, '
                              'де знаходиться авто: ')

    await state.set_state(FSMFillCarInfo.fill_city)


@router.message(StateFilter(FSMFillCarInfo.fill_city), F.text)
async def process_fill_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer(text='Дякую!\n\nНапишіть рік випуску авто:')
    await state.set_state(FSMFillCarInfo.fill_year_of_build)


@router.message(StateFilter(FSMFillCarInfo.fill_city))
async def process_fill_city_error(message: Message):
    await message.answer(text='Те, що Ви відправили, не схоже на назву міста\n'
                              'Спробуйте ще раз: ')


@router.message(StateFilter(FSMFillCarInfo.fill_year_of_build), F.text)
async def process_year_of_build_sent(message: Message, state: FSMContext):
    await state.update_data(year_of_build=message.text)
    await message.answer(text='Вкажіть пробіг авто: ')
    await state.set_state(FSMFillCarInfo.fill_range)

# Этот хэндлер будет срабатывать, если во время ввода имени
# будет введено что-то некорректное
@router.message(StateFilter(FSMFillCarInfo.fill_model))
async def warning_not_name(message: Message):
    await message.answer(text='Те, що Ви відправили, не схоже на марку та модель авто\n\n'
                              'Спробуйте ще раз\n\n'
                              'Мінімальна кількість символів - 4\n\n'
                              'Для відміни відправки форми - '
                              'відправте команду /cancel')


@router.message(StateFilter(FSMFillCarInfo.fill_range), F.text)
async def adding_range(message: Message, state: FSMContext):
    await state.update_data(range=message.text)
    await message.answer(text='Напишіть тип палива двигуна,\n'
                              'або електро/гібрид:')
    await state.set_state(FSMFillCarInfo.fill_engine_type)


@router.message(StateFilter(FSMFillCarInfo.fill_range))
async def error_range_adding(message: Message):
    await message.answer(text="Те, що Ви вказали, не схоже на пробіг\n"
                              "Вкажіть пробіг: ")


@router.message(StateFilter(FSMFillCarInfo.fill_engine_type), F.text)
async def process_engine_type_sent(message: Message, state: FSMContext):
    await state.update_data(engine_type=message.text)
    await message.answer(text='Дякую!\n'
                              'Тепер напишить обʼєм двигуна, або для електро кількіть кВт:')
    await state.set_state(FSMFillCarInfo.fill_capacity)


@router.message(StateFilter(FSMFillCarInfo.fill_capacity), F.text)
async def process_of_add_capacity(message: Message, state: FSMContext):
    await state.update_data(engine_capacity=message.text)
    # buttons
    await message.answer(text='Напишіть тип коробки передач:')
    await state.set_state(FSMFillCarInfo.fill_gear_box_type)


# that handler will work if add correct type of gearbox
@router.message(StateFilter(FSMFillCarInfo.fill_gear_box_type))
async def process_fill_gear_box_type(message: Message, state: FSMContext):
    await state.update_data(gear_box=message.text)
    await message.answer(text='Напишіть VIN або державний номер авто: ')
    await state.set_state(FSMFillCarInfo.fill_vin_or_numbers)


# That will star if correct ansfer for gearbox
@router.message(StateFilter(FSMFillCarInfo.fill_vin_or_numbers), lambda massage: len(massage.text) >= 5)
async def process_vin_or_number(message: Message, state: FSMContext):
    await state.update_data(vin_or_num=message.text)
    yes_but = InlineKeyboardButton(text='Вірно ✅',
                                   callback_data='yes')
    no_but = InlineKeyboardButton(text='Ввести ще раз 🔁',
                                  callback_data='no')
    keyboard: list[list[InlineKeyboardButton]] = [
        [yes_but, no_but]]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(text=f"Підтвердіть коректність введених даних {message.text}",
                         reply_markup=markup)
    await state.set_state(FSMFillCarInfo.confirm_vin_state)


@router.callback_query(StateFilter(FSMFillCarInfo.confirm_vin_state), Text(text=['yes', 'no']))
async def confirm_vin(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'yes':
        await callback.message.delete()
        await callback.message.answer(text='Додайте від 4 до 10 фото:')
        await state.set_state(FSMFillCarInfo.upload_photo)
    elif callback.data == 'no':
        await callback.message.delete()
        await callback.message.answer(text='Напишіть VIN або державний номер авто: ')
        await state.set_state(FSMFillCarInfo.fill_vin_or_numbers)


@router.message(StateFilter(FSMFillCarInfo.fill_vin_or_numbers))
async def incorrect_num_or_vin(message: Message):
    await message.answer(text="Вибачте, це не схоже на номер чи VIN\n"
                              "Спробуйте ще раз")


@router.callback_query(StateFilter(FSMFillCarInfo.confirm_vin_state))
async def confirm_vin_error(callback: CallbackQuery):
    await callback.message.answer(text='Ви не підтвердели коррекність данних\n'
                                       'Ви можете підтвердити у повідомленні вище.')


from aiogram_media_group import media_group_handler


# Прцесс добаления фото/ сейчас есть бага если добалять все фото разом то у нас много сообщений о том что добавь фото
# добавить вопрос хочет ли еще фото юзер
async def _process_and_update_photos(messages: list[Message], state: FSMContext):
    data = await state.get_data()
    # Initialize photos list if it doesn't exist
    photos_list = data.get('photos', [])

    # Process received messages
    for message in messages:
        if len(photos_list) < 10 and message.photo:
            photos_list.append(message.photo[-1].file_id)

    # Update state with the new list of photos
    await state.update_data(photos=photos_list)

    # Use the last message for replies
    last_message = messages[-1]
    num_photos = len(photos_list)

    if num_photos >= 10:
        # Reached the maximum number of photos
        await last_message.answer(text="Ви додали максимальну кількість фото!", reply_markup=ReplyKeyboardRemove())
        yes_but = InlineKeyboardButton(text="Додати відео ✅", callback_data='yes')
        no_but = InlineKeyboardButton(text='Пропустити ➡️', callback_data='no')
        keyboard: list[list[InlineKeyboardButton]] = [[yes_but, no_but]]
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await last_message.answer(text="Чи бажаєте Ви додати відеоогляд авто?", reply_markup=markup)
        await state.set_state(FSMFillCarInfo.upload_video_question)
    elif num_photos >= 4:
        # Sufficient photos, but less than 10. Allow adding more or stopping.
        button_stop: KeyboardButton = KeyboardButton(text='Більше не додавати 🛑')
        keyboard: ReplyKeyboardMarkup = ReplyKeyboardMarkup(keyboard=[[button_stop]], resize_keyboard=True)
        await last_message.answer(reply_markup=keyboard, text='Ви можете додати ще фото\n'
                                                              'Якщо ви не бажаєте додавати більше фото - натисніть  '
                                                              '\n"Більше не додавати 🛑"')
    else: # num_photos < 4
        # Not enough photos yet.
        await last_message.answer(f"Потрібно додати ще як мінімум {4 - num_photos} фото.")


# Media group handler
@router.message(StateFilter(FSMFillCarInfo.upload_photo), F.media_group_id)
@media_group_handler
async def process_photo_group_sent(messages: list[Message], state: FSMContext):
    await _process_and_update_photos(messages, state)


# Single photo handler
@router.message(StateFilter(FSMFillCarInfo.upload_photo), F.photo)
async def process_single_photo_sent(message: Message, state: FSMContext):
    await _process_and_update_photos([message], state)


@router.message(StateFilter(FSMFillCarInfo.upload_photo),
            Text(text='Більше не додавати 🛑'))
async def process_of_change_state_to_fill_price(message: Message, state: FSMContext):
    await message.answer(text="Фото збережені.",
                         reply_markup=ReplyKeyboardRemove())
    yes_but = InlineKeyboardButton(text="Додати відео ✅",
                                   callback_data='yes')
    no_but = InlineKeyboardButton(text='Пропустити ➡️',
                                  callback_data='no')
    keyboard: list[list[InlineKeyboardButton]] = [
        [yes_but, no_but]]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(text="Чи бажаєте Ви додати відеоогляд авто?",
                         reply_markup=markup)

    await state.set_state(FSMFillCarInfo.upload_video_question)


@router.callback_query(StateFilter(FSMFillCarInfo.upload_video_question), Text(text=['yes', 'no']))
async def process_of_upload_video_question(callback: CallbackQuery, state: FSMContext):
    if callback.data == 'yes':
        await callback.message.delete()
        await callback.message.answer(text='Додайте відео: ')
        await state.set_state(FSMFillCarInfo.upload_video)
    elif callback.data == 'no':
        await callback.message.delete()
        await callback.message.answer(text='Напишіть декілька слів про ваше авто(підкраси, стан кузову, технічний стан,'
                                           ' комплектація):')
        await state.set_state(FSMFillCarInfo.fill_some_info)


@router.message(StateFilter(FSMFillCarInfo.upload_photo))
async def error_upload_photo(message: Message):
    await message.answer(text="Це не схоже на фото.\n"
                              "Додайте від 4 до 10 фото:")


@router.message(StateFilter(FSMFillCarInfo.upload_video), F.video)
async def process_of_upload_video(message: Message, state: FSMContext):
    await state.update_data(video=message.video.file_id)
    await message.answer(text='Напишіть декілька слів про ваше авто(підкраси, стан кузову, технічний стан,'
                              ' комплектація):')
    await state.set_state(FSMFillCarInfo.fill_some_info)


@router.message(StateFilter(FSMFillCarInfo.upload_video))
async def error_vidoe_upload(message: Message):
    await message.answer(text='Це не схоже на відео.\n'
                              'Спробуйте ще раз.')


@router.message(StateFilter(FSMFillCarInfo.fill_some_info), F.text)
async def process_adding_some_info(message: Message, state: FSMContext):
    await state.update_data(car_info=message.text)
    await message.answer(text='Вкажіть ціну: ')
    await state.set_state(FSMFillCarInfo.fill_price)


@router.message(StateFilter(FSMFillCarInfo.fill_some_info))
async def error_info_filling(message: Message):
    await message.answer(text="Напишіть декілька слів про ваше авто (підкраси, стан кузову, технічний стан, "
                              "комплектація):")


async def send_car_info_to_manager(user_id: int, bot: Bot, chat_id: str):
    user_data = user_dict.get(user_id)
    if not user_data:
        return

    contact_info = f'@{user_data["user_url"]}' if user_data.get("user_url") else user_data.get("contact", "Не вказано")
    caption = (
        f'Імʼя: {user_data["user_name"]}\n'
        f'Контакт: {contact_info}\n'
        f'Локація авто: {user_data["city"]}\n'
        f'Авто: {user_data["model"]}\n'
        f'Двигун(Тип/Паливо): {user_data["engine_type"]}\n'
        f'Пробіг: {user_data["range"]}\n'
        f'Обʼєм: {user_data["engine_capacity"]}\n'
        f'Коробка: {user_data["gear_box"]}\n'
        f'Рік: {user_data["year_of_build"]}\n'
        f'VIN/Номер: {user_data["vin_or_num"]}\n'
        f'Ціна: {user_data["price"]}\n'
        f'Про авто: {user_data["car_info"]}'
    )

    media = []
    photos = user_data.get("photos", [])
    video = user_data.get("video")

    limit = 10
    if video:
        media.append(InputMediaVideo(media=video))
        limit -= 1

    for photo_file_id in photos[:limit]:
        media.append(InputMediaPhoto(media=photo_file_id))

    # Now, if media is not empty, add the caption to the first element
    if media:
        media[0].caption = caption
        await bot.send_media_group(chat_id=chat_id, media=media)
    elif caption: # Fallback if no media
        await bot.send_message(chat_id=chat_id, text=caption)

    reply_button = InlineKeyboardButton(
        text="💬 Відповісти клієнту",
        callback_data=f"ans:{user_id}"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[reply_button]])
    await bot.send_message(
        chat_id=chat_id,
        text="Нова заявка!",
        reply_markup=keyboard
    )


@router.message(StateFilter(FSMFillCarInfo.fill_price), F.text)
async def process_fill_price(message: Message,
                             state: FSMContext,
                             bot: Bot,
                             chat_id: str):
    await state.update_data(price=message.text)
    user_dict[message.from_user.id] = await state.get_data()
    if user_dict[message.from_user.id]["user_url"]:
        await message.answer(text='Дякую. Менеджер звʼяжеться з вами.')
        start_button = InlineKeyboardButton(text='Повторити 🔄',
                                            callback_data='fillform')
        keyboard: list[list[InlineKeyboardButton]] = [[start_button]]
        markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
        await message.answer(text="Для повторної відправки форми - натискайте на кнопку ⬇️", reply_markup=markup)
        await state.clear()
        
        await send_car_info_to_manager(message.from_user.id, bot, chat_id)
    else:
        await message.answer(text='Вкажіть Контактний номер')
        await state.set_state(FSMFillCarInfo.fill_contact_info)


@router.message(StateFilter(FSMFillCarInfo.fill_price))
async def error_for_price(message: Message):
    await message.answer(text="ВкажіTь ціну: ")


# This handler works if user doesn`t have user_name and added valid number
@router.message(StateFilter(FSMFillCarInfo.fill_contact_info), F.text,
            lambda x: x.text.isdigit() and 10 <= len(x.text) <= 12)
async def process_add_contact(message: Message, state: FSMContext, bot: Bot, chat_id: str):
    await state.update_data(contact=message.text)
    user_dict[message.from_user.id] = await state.get_data()
    await message.answer(text='Дякую. Менеджер звʼяжеться з вами.')
    start_button = InlineKeyboardButton(text='Повторити 🔄',
                                        callback_data='fillform')
    keyboard: list[list[InlineKeyboardButton]] = [[start_button]]
    markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    await message.answer(text="Для повторної відправки форми - натискайте на кнопку ⬇️", reply_markup=markup)
    await state.clear()
    
    await send_car_info_to_manager(message.from_user.id, bot, chat_id)


# Handler works when user sent not valid number
@router.message(StateFilter(FSMFillCarInfo.fill_contact_info))
async def invalid_number(message: Message):
    await message.answer(text="Схоже Ви ввели не коректний номер.\n"
                              "Номер має складати від 10 до 12 символів\n"
                              "Спробуйте ще раз\n"
                              "Якщо ви вводили пчинаючи з ʼ+ʼ, приберіть ʼ+ʼ")
