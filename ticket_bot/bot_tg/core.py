from aiogram import Bot, Dispatcher, Router
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode

from os import getenv

from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import DeleteWebhook
from dotenv import load_dotenv

import asyncio


load_dotenv()


bot_ = Bot(
    token=getenv('BOT_TOKEN_API'),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)


async def start_bot() -> None:
    await bot_(DeleteWebhook(drop_pending_updates=True))
    await asyncio.gather(dp.start_polling(bot_))
