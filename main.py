import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage, Redis
from environs import Env

from handlers import common, survey, admin


def main():
    # Logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(filename)s:%(lineno)d #%(levelname)-8s '
               '[%(asctime)s] - %(name)s - %(message)s')

    # Logger for the application
    logger = logging.getLogger(__name__)

    # Load environment variables
    env = Env()
    env.read_env()
    bot_token = env('BOT_TOKEN')
    redis_url = env('REDIS_URL')
    chat_id = env('CHAT_ID')

    # Initialize Redis and storage
    redis: Redis = Redis.from_url(redis_url)
    storage: RedisStorage = RedisStorage(redis=redis)

    # Initialize Bot and Dispatcher
    bot: Bot = Bot(token=bot_token, parse_mode='HTML')
    dp: Dispatcher = Dispatcher(storage=storage, chat_id=chat_id)

    # Include routers
    dp.include_router(admin.router)
    dp.include_router(common.router)
    dp.include_router(survey.router)

    # Start the bot
    logger.info('Starting bot')
    try:
        dp.run_polling(bot)
    except Exception as e:
        logger.error(f'An error occurred: {e}')


if __name__ == '__main__':
    main()