from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from lexicon.lexicon import LEXICON_RU
from keyboards.menu_buttons import menu_button

def create_inline_kb(width: int,
                              *args: str,
                              **kwargs: str) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()

    buttons: list[InlineKeyboardButton] = []

    if args:
        for button in args:
            buttons.append(InlineKeyboardButton(
                text=LEXICON_RU[button] if button in LEXICON_RU else button,
                callback_data=button))
    if kwargs:
        for button, text in kwargs.items():
            buttons.append(InlineKeyboardButton(
                text=text,
                callback_data=button))
        
    kb_builder.row(*buttons, width=width)

    return kb_builder.as_markup()

def create_dymamic_inline_kb(start_idx: int, width: int,
                              *args: str,
                              **kwargs: str) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()

    buttons: list[InlineKeyboardButton] = []

    if args: 
        for button in range(start_idx, min(start_idx + width * 7, len(args))):
            _id, name = args[button]
            
            buttons.append(InlineKeyboardButton(
                text=name,
                callback_data=f'null_{_id}')
            )

        if start_idx > 0:
            buttons.append(InlineKeyboardButton(
                text=LEXICON_RU['back_button'], 
                callback_data=f"back_{max(start_idx - width * 7, 0)}")
            )
        
        if start_idx + width * 7 < len(args):
            buttons.append(InlineKeyboardButton(
                text=LEXICON_RU['next_button'], 
                callback_data=f"forward_{start_idx + width * 7}")
            )

        buttons.append(menu_button)
        
    kb_builder.row(*buttons, width=width)

    return kb_builder.as_markup()