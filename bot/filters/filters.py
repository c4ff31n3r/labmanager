from aiogram.filters import BaseFilter
from aiogram.types import Message

from database.database import is_user_register

# Фильтр, проверяющий зарегестрирован ли пользователь
class IsUserRegister(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        return is_user_register(user_id=message.from_user.id)