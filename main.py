import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, Redis
from aiogram.types import BotCommand, BotCommandScopeChat, BotCommandScopeDefault
from environs import Env

from handlers import common, survey, admin


async def set_bot_commands(bot: Bot, chat_id: str):
    """Регистрация команд в меню"""
    # Команды для всех (в личке)
    user_commands = [
        BotCommand(command="start", description="Запустити бота"),
        BotCommand(command="fillform", description="Заповнити анкету авто"),
        BotCommand(command="help", description="Допомога"),
    ]
    await bot.set_my_commands(commands=user_commands, scope=BotCommandScopeDefault())

    # Команды для менеджеров (в группе)
    if chat_id:
        try:
            admin_commands = [
                BotCommand(command="close", description="Закрити діалог"),
                BotCommand(command="delete", description="Видалити топік"),
            ]
            await bot.set_my_commands(
                commands=admin_commands, 
                scope=BotCommandScopeChat(chat_id=int(chat_id))
            )
        except Exception as e:
            logging.error(f"Failed to set admin commands: {e}")

async def main():
    # Logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(filename)s:%(lineno)d #%(levelname)-8s [%(asctime)s] - %(name)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

    # Logger for the application
    logger = logging.getLogger(__name__)
    logger.info('Initializing bot...')

    # Load environment variables
    env = Env()
    env.read_env()
    bot_token = env.str('BOT_TOKEN', None)
    redis_url = env.str('REDIS_URL', 'redis://localhost:6379/0')
    chat_id = env.str('CHAT_ID', None)
    
    if not bot_token:
        logger.error("BOT_TOKEN is not set!")
        return

    logger.info(f"Using Redis at {redis_url}")
    logger.info(f"Target Chat ID: {chat_id}")

    # Initialize Redis and storage
    try:
        redis: Redis = Redis.from_url(redis_url)
        storage: RedisStorage = RedisStorage(redis=redis)
        logger.info("Redis storage initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {e}")
        return

    # Initialize Bot and Dispatcher
    bot: Bot = Bot(token=bot_token, parse_mode='HTML')
    dp: Dispatcher = Dispatcher(storage=storage, chat_id=chat_id)

    # Set bot commands
    await set_bot_commands(bot, chat_id)

    # Include routers
    dp.include_router(admin.router)
    dp.include_router(common.router)
    dp.include_router(survey.router)

    # Start the bot
    logger.info('Starting bot')
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f'An error occurred: {e}')


if __name__ == '__main__':
    asyncio.run(main())