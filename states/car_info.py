from aiogram.filters.state import State, StatesGroup


# Створюємо клас, успадкований від StatesGroup, для групи станів нашої FSM
class FSMFillCarInfo(StatesGroup):
    fill_model = State()  # Стан очікування введення марки авто
    fill_city = State()
    fill_year_of_build = State()  # Стан очікування введення року випуску авто
    fill_range = State()  # пробіг авто
    fill_engine_type = State()  # Стан введення типу двигуна
    fill_capacity = State()  # Стан введення об'єму або потужності
    fill_gear_box_type = State()  # Стан очікування введення типу коробки
    fill_vin_or_numbers = State()  # Стан очікування вибору чи були ДТП
    confirm_vin_state = State()
    upload_photo = State()  # Стан очікування завантаження фото
    upload_video_question = State()
    upload_video = State()
    fill_some_info = State()
    fill_contact_info = State()  # Цей стан активується, якщо у користувача немає імені користувача
    fill_price = State()  # Стан очікування заповнення ціни на авто
