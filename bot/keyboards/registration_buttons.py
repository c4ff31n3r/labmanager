from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext

from lexicon.lexicon import LEXICON_RU

registration_button = InlineKeyboardButton(
    text=LEXICON_RU['registration_button'],
    callback_data='registration_button'
)

full_name_button = InlineKeyboardButton(
    text=LEXICON_RU['full_name_button'],
    callback_data='full_name_button'
)
group_button = InlineKeyboardButton(
    text=LEXICON_RU['group_button'],
    callback_data='group_button'
)
accept_button = InlineKeyboardButton(
    text=LEXICON_RU['accept_button'],
    callback_data='accept_button'
)
cancel_button = InlineKeyboardButton(
    text=LEXICON_RU['cancel_button'],
    callback_data='cancel_button'
)

async def create_registration_keyboard(state: FSMContext):

    data = await state.get_data()

    if 'full_name' in data:
        full_name_button.text = data['full_name']
    else:
        full_name_button.text = LEXICON_RU['full_name_button']
    
    if 'group' in data:
        group_button.text = data['group']
    else:
        group_button.text = LEXICON_RU['group_button']

    list_kb = [[full_name_button], [group_button], [cancel_button]]

    if 'full_name' in data and 'group' in data:
        list_kb.append([accept_button])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=list_kb
    )

    return keyboard