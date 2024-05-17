from aiogram.types import InlineKeyboardButton


from lexicon.lexicon import LEXICON_RU

menu_button = InlineKeyboardButton(
    text=LEXICON_RU['menu_button'],
    callback_data='menu_button'
)