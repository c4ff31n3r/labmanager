from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.types.input_file import BufferedInputFile
from aiogram.fsm.state import default_state
from aiogram.fsm.context import FSMContext

from config_data.config import RegistrationStates, GenerateQrCodeStates, InfoLabs
from database.database import (insert_db, is_user_register, get_user_data, get_all_subjects, 
    get_labs_with_subject_id, update_labs, get_status_lab, get_lab_with_lab_id, get_subject_with_id, get_teacher_with_id)
from other.other import generate_qr_code, get_url, get_status_with_id

from keyboards.registration_buttons import (registration_button, create_registration_keyboard)
from keyboards.menu_buttons import menu_button
from keyboards.keyboard import create_inline_kb, create_dymamic_inline_kb

from filters.filters import IsUserRegister

from lexicon.lexicon import LEXICON_RU

import re, os

router = Router()
    
# Команда /start, приветствие
@router.message(CommandStart(), StateFilter(default_state))
async def process_start_command(message: Message):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[registration_button], [menu_button]]
    )

    await message.answer(
        text=LEXICON_RU[message.text],
        reply_markup=keyboard
    )
    
# Команда /help для просмотра всех доступных команд 
@router.message(Command(commands='help'), StateFilter(default_state))
async def process_help_command(message: Message):
    await message.delete()

    await message.answer(LEXICON_RU[message.text])
    
# Меню регистрации в базе денных через команду    
@router.message(StateFilter(default_state), Command(commands='register'))
async def press_register_command(message: Message, state: FSMContext):
    await message.delete()


    if is_user_register(user_id=message.from_user.id):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[menu_button]]
        )
        await message.answer(
            text=LEXICON_RU['failed_start_register'],
            reply_markup=keyboard
        )
    else:
        keyboard = await create_registration_keyboard(state=state)

        await message.answer(
            text=LEXICON_RU['register_text'],
            reply_markup=keyboard
        )

        #Установка статуса ожидания выбора кнопки
        await state.set_state(RegistrationStates.wait_select)

# Меню регистрации в базе данных через кнопку
@router.callback_query(StateFilter(default_state), F.data == 'registration_button')
async def process_click_register_button(callback: CallbackQuery, state: FSMContext):

    await callback.message.delete()

    if is_user_register(user_id=callback.from_user.id):

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[menu_button]]
        )
        await callback.message.answer(
            text=LEXICON_RU['failed_start_register'],
            reply_markup=keyboard
        )
    else:
        keyboard = await create_registration_keyboard(state=state)

        await callback.message.answer(
            text=LEXICON_RU['register_text'],
            reply_markup=keyboard
        )

        #Установка статуса ожидания выбора кнопки
        await state.set_state(RegistrationStates.wait_select)

# Регистрация, нажатие на кнопку для ввода ФИО
@router.callback_query(StateFilter(RegistrationStates.wait_select), F.data == 'full_name_button')
async def process_click_enter_full_name(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        text=LEXICON_RU['enter_full_name']
    )

    await state.set_state(RegistrationStates.fill_full_name)

# Регистрация, нажатие на кнопку для ввода группы
@router.callback_query(StateFilter(RegistrationStates.wait_select), F.data == 'group_button')
async def process_click_enter_group(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await callback.message.answer(
        text=LEXICON_RU['enter_group']
    )

    await state.set_state(RegistrationStates.fill_group)

# Регистрация, нажатие на кнопку отмены регистрации
@router.callback_query(StateFilter(RegistrationStates.wait_select), F.data == 'cancel_button')
async def process_click_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text=LEXICON_RU['register_text_cancel']
    )

    await state.clear()

# Обработка ошибки, если пользователь вводит текст, а не нажимает на кнопку
@router.message(StateFilter(RegistrationStates.wait_select))
async def process_click_button_error(message: Message):
    await message.answer(LEXICON_RU['error_message'])

# Регистрация, ввод ФИО
@router.message(StateFilter(RegistrationStates.fill_full_name))
async def process_enter_full_name(message: Message, state: FSMContext):

    if not(re.match(r'^[А-ЯЁA-Z][а-яёa-z]+\s[А-ЯЁA-Z][а-яёa-z]+\s[А-ЯЁA-Z][а-яёa-z]+$', message.text)):
        await message.answer(
            text=LEXICON_RU['incorrect_input']
        )
    else: 
        await message.delete()

        await state.update_data(full_name=message.text)

        keyboard = await create_registration_keyboard(state=state)

        await message.answer(
            text=LEXICON_RU['register_text_after'],
            reply_markup=keyboard
        )

        await state.set_state(RegistrationStates.wait_select)

# Регистрация, ввод группы
@router.message(StateFilter(RegistrationStates.fill_group))
async def process_enter_group(message: Message, state: FSMContext):

    if not(re.match(r'^[А-Яа-я]{2,4}[а-я]{1}-\d{4}-\d{2}-\d{2}$', message.text)):
        await message.answer(text=LEXICON_RU['incorrect_input'])
    else: 
        await message.delete()

        await state.update_data(group=message.text)

        keyboard = await create_registration_keyboard(state=state)

        await message.answer(
            text=LEXICON_RU['register_text_after'],
            reply_markup=keyboard
        )

        await state.set_state(RegistrationStates.wait_select)

# Регистрация, нажатие на кнопка завершения регистрации
@router.callback_query(StateFilter(RegistrationStates.wait_select), F.data == 'accept_button')
async def process_click_accept_button(callback: CallbackQuery, state: FSMContext):

    await callback.message.delete()

    data = await state.get_data()

    if 'full_name' in data and 'group' in data:
        status = insert_db(user_id=callback.from_user.id, chat_id=callback.message.chat.id, 
                  full_name=data['full_name'], group_name=data['group'])
        
        if status:
            # Успешная регистрация 
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[[menu_button]]
            )

            await callback.message.answer(
                text=LEXICON_RU['registration_confirm'].format(data['full_name'], data['group'].replace('-', '\-')),
                reply_markup=keyboard
            )
        else:
            await callback.message.answer(
                text=LEXICON_RU['mysql_error'] + ' ' + LEXICON_RU['registration_cancel']
            )

    else:
        await callback.message.answer(
            text=LEXICON_RU['unknown_error'] + ' ' + LEXICON_RU['registration_cancel']
        )

    await state.clear()

# Обработка ошибки, если пользователь нажимает на кнопку, а не вводит текст!
@router.callback_query(StateFilter(RegistrationStates.fill_full_name, RegistrationStates.fill_group))
async def process_enter_data_error(callback: CallbackQuery):
    await callback.message.answer(LEXICON_RU['error_click_button'])

# Кнопка для открытия главного меню
@router.callback_query(F.data == 'menu_button')
async def process_click_menu_button(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()

    if not('delete_message_flag' in data):
        await callback.message.delete()
    await state.clear()

    await generate_menu(message=callback.message, user_id=callback.from_user.id)

# Команда для открытия главного меню
@router.message(Command(commands='menu'))
async def process_click_menu_button(message: Message, state: FSMContext):
    await state.clear()
    await generate_menu(message=message, user_id=message.from_user.id)
# Отображение меню
async def generate_menu(message: Message, user_id: str):
    #await message.delete()

    if not(is_user_register(user_id=user_id)):
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[registration_button]]
        )

        await message.answer(
            text=LEXICON_RU['failed_enter_menu'],
            reply_markup=keyboard
        )
    else:
        keyboard = create_inline_kb(1, 'generate_qr_button', 'check_info_button')
        student = get_user_data(user_id=user_id)

        await message.answer(
            text=LEXICON_RU['menu_text'].format(student[2], student[3].replace('-', '\-')),
            reply_markup=keyboard
        )

# Кнопка генерации QR-code
@router.callback_query(StateFilter(default_state), F.data == 'generate_qr_button', IsUserRegister())
async def process_click_generate_qr_button(callback: CallbackQuery, state: FSMContext):
    subjects = get_all_subjects()

    # Если список предметов пустой
    if not(subjects):
        await callback.answer(
            text=LEXICON_RU['error_no_subjects'],
            show_alert=True
        )
    # Если список предметов не пустой
    else: 
        await callback.message.delete()

        await state.set_state(GenerateQrCodeStates.select_subject)
        await state.update_data(subjects=subjects)

        keyboard = create_dymamic_inline_kb(0, 2, *subjects)
        await callback.message.answer(
            text=LEXICON_RU['select_subject'].format(len(subjects)),
            reply_markup=keyboard
        )

# Кноки, выбор предмета
@router.callback_query(StateFilter(GenerateQrCodeStates.select_subject), IsUserRegister())
async def process_click_select_subject(callback: CallbackQuery, state: FSMContext):
    subject, idx = callback.data.split('_')
    labs = get_labs_with_subject_id(subject_id=idx)

    data = await state.get_data()

    if subject == 'forward':
        await callback.message.delete()
        subjects = data['subjects'];

        keyboard = create_dymamic_inline_kb(int(idx), 2, *subjects)
        await callback.message.answer(
            text=LEXICON_RU['select_subject'].format(len(subjects)),
            reply_markup=keyboard
        )
    elif subject == 'back':
        await callback.message.delete()
        subjects = data['subjects'];
        keyboard = create_dymamic_inline_kb(int(idx), 2, *subjects)
        await callback.message.answer(
            text=LEXICON_RU['select_subject'].format(len(subjects)),
            reply_markup=keyboard
        )
    else:
        subject_name = get_subject_with_id(subject_id=idx)[1]
        # Если лабораторный по данному предмету нет
        if not(labs):
            await callback.answer(
                text=LEXICON_RU['error_no_labs'].format(subject_name),
                show_alert=True
            )
        # Если лабораторные работы есть
        else:
            # Из всех данных получить берём name и id предмета
            _labs = [(i[0], i[1]) for i in labs]

            await callback.message.delete()

            await state.update_data(subject_name=subject_name,
                                    subject_id=idx)

            await state.set_state(GenerateQrCodeStates.select_labs)

            await state.update_data(labs=_labs)

            keyboard = create_dymamic_inline_kb(0, 2, *_labs)

            await callback.message.answer(
                text=LEXICON_RU['select_labs'].format(len(_labs)),
                reply_markup=keyboard
            )

# Кнопки, выбор лабораторной работы
@router.callback_query(StateFilter(GenerateQrCodeStates.select_labs), IsUserRegister())
async def process_click_select_labs(callback: CallbackQuery, state: FSMContext):
    lab_name, idx = callback.data.split('_')
    await callback.message.delete()

    data = await state.get_data()

    if lab_name in ['forward', 'back']:
        labs = data['labs']
        keyboard = create_dymamic_inline_kb(int(idx), 2, *labs)
        await callback.message.answer(
            text=LEXICON_RU['select_labs'].format(len(labs)),
            reply_markup=keyboard
        )
    else:

        lab = get_lab_with_lab_id(lab_id=idx)
        if lab[2]:
            teacher = get_teacher_with_id(teacher_id=lab[2])[3]
        else: 
            teacher = 'Unknown'

        keyboard = create_inline_kb(1, 'generate_qr_button', 'menu_button')

        await state.update_data(lab_name=lab[1],
                                lab_id=idx,
                                teacher=teacher)
        
        await state.set_state(GenerateQrCodeStates.generate_lab)

        await callback.message.answer(
            text=LEXICON_RU['after_select_labs'].format(data['subject_name'], lab[1], teacher),
            reply_markup=keyboard
        )

# Кнопка для генерации QR-code
@router.callback_query(StateFilter(GenerateQrCodeStates.generate_lab), IsUserRegister(), F.data == 'generate_qr_button')
async def process_click_generate_qr(callback: CallbackQuery, state: FSMContext):
    await callback.message.delete()

    data = await state.get_data()
    await state.clear()

    url = get_url(callback.from_user.id, data['lab_id'])

    if generate_qr_code(user_id=callback.from_user.id, url=url):
        photo = BufferedInputFile.from_file(path=f'handlers/{callback.from_user.id}.jpg')

        url_button = InlineKeyboardButton(
            text=LEXICON_RU['url_text'],
            url=url
        )

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[menu_button], [url_button]]
        )
        await callback.message.answer_photo(
            photo=photo,
            caption=LEXICON_RU['qr_caption'].format(data['subject_name'], data['lab_name'], data['teacher']),
            reply_markup=keyboard
        )
        os.remove(f'handlers/{callback.from_user.id}.jpg')

        await state.update_data(delete_message_flag=1)

        # Обновляем статус при генерации QR-code только если он был 0
        if int(get_status_lab(user_id=callback.from_user.id, lab_id=data['lab_id'])) == 0:
            update_labs(user_id=callback.from_user.id, lab_id=data['lab_id'], status=1)

# Кнопк в главном меню просмотреть все лаборатоорные работы
@router.callback_query(StateFilter(default_state), F.data == 'check_info_button', IsUserRegister())
async def process_click_show_user_labs(callback: CallbackQuery, state: FSMContext):
    user_data = get_user_data(user_id=callback.from_user.id)

    try:
        user_labs = list(map(int, user_data[5].split(',')))

        if not(sum(user_labs)):
            raise Exception('Sum is zero')

        labs = []

        for i in range(0, len(user_labs)):
            if user_labs[i] > 0:
                lab = get_lab_with_lab_id(i + 1)
                labs.append((lab[0], lab[1]))

        await state.set_state(InfoLabs.select_labs)
        await state.update_data(labs=labs, update_data=user_data)   
        
        keyboard = create_dymamic_inline_kb(0, 2, *labs)
        await callback.message.answer(
            text=LEXICON_RU['all_user_labs'].format(len(labs)),
            reply_markup=keyboard
        )
    except Exception:
        await callback.answer(
            text=LEXICON_RU['error_no_user_labs'],
            show_alert=True
        )

# Кнопк в главном меню просмотреть информацию по конкретной лабораторной работе
@router.callback_query(StateFilter(InfoLabs.select_labs), IsUserRegister())
async def process_click_show_info_labs(callback: CallbackQuery, state: FSMContext):
    lab, idx = callback.data.split('_')

    data = await state.get_data()
    
    if lab == 'forward':
        labs = data['labs']
        keyboard = create_dymamic_inline_kb(int(idx), 2, *labs)
        await callback.message.answer(
            text=LEXICON_RU['all_user_labs'].format(len(labs)),
            reply_markup=keyboard
        )
    elif lab == 'back':
        labs = data['labs']
        keyboard = create_dymamic_inline_kb(int(idx), 2, *labs)
        await callback.message.answer(
            text=LEXICON_RU['all_user_labs'].format(len(labs)),
            reply_markup=keyboard
        )
    else:
        lab = get_lab_with_lab_id(lab_id=idx)
        subject = get_subject_with_id(lab[5])[1]
        if lab[2]:
            teacher = get_teacher_with_id(teacher_id=lab[2])[3]
        else: 
            teacher = 'Unknown'

        user_data = data['update_data']
        status = user_data[5].split(',')[int(idx) - 1]

        message = get_status_with_id(status=status)

        url = get_url(user_id=callback.from_user.id, lab_id=idx)

        url_button = InlineKeyboardButton(
            text=LEXICON_RU['url_text'],
            url=url
        )   

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[[menu_button], [url_button]]
        )
        await callback.message.answer(
            text=LEXICON_RU['info_user_lab'].format(subject, lab[1], teacher, message),
            reply_markup=keyboard
        )

        await state.clear()