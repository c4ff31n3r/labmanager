import asyncio
import logging

from config_data.config import Config, load_config
from handlers import user_handlers

from aiogram import Bot, Dispatcher

logger = logging.getLogger(__name__)

async def main():
    #Конфирурация логирования
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(filename)s:%(lineno)d #%(levelname)-8s'
               '[%(asctime)s] - %(name)s - %(message)s'
        )
    
    logger.info('Starting Bot') 

    #Загрузка конфигурации
    config: Config = load_config()

    bot = Bot(
        token=config.tg_bot.token,
        parse_mode="MarkdownV2"
    )
    dp = Dispatcher()

    dp.include_router(user_handlers.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())