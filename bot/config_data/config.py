from dataclasses import dataclass
from aiogram.fsm.state import State, StatesGroup
import os
from dotenv import load_dotenv


@dataclass
class TelegramBot():
    token: str

@dataclass
class Config():
    tg_bot: TelegramBot

def load_config():
    load_dotenv()
    return Config(
        tg_bot=TelegramBot(
            token=os.getenv('BOT_TOKEN')
        )
    )

# Состояния регистрации пользователя
class RegistrationStates(StatesGroup):
    wait_select = State() # Состояние выбора, что ввести (ФИО или группу)
    fill_full_name = State() # Состояние ожидания выбора ФИО
    fill_group = State() # Состояние ожидания выбора группы

# Состояния генерации QR-code
class GenerateQrCodeStates(StatesGroup):
    select_subject = State() # Состоние выбора предмета
    select_labs = State() # Состояние выбора лабораторной работы
    generate_lab = State() # Состояние выбора (генерация или возват в главное меню)

class InfoLabs(StatesGroup):
    select_labs = State() # Состояние выбора лабораторной работы