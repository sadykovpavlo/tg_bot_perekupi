from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

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
