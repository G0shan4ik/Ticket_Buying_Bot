from aiogram import Bot, Dispatcher, Router
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode

from ticket_bot.bot_tg.helpers import read_data_from_json
from ticket_bot.parsers.parser import BuyingTicketsNikulina

from os import getenv

from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.methods import DeleteWebhook
from dotenv import load_dotenv

import asyncio


load_dotenv()

admin_id =getenv('ADMIN')

bot_ = Bot(
    token=getenv('BOT_TOKEN_API'),
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
dp.include_router(router)


async def check_pars_event() -> None:
    """
        The function that runs all 'active' events from the users_filters
        file is launched at program startup and runs once.

    :return: None
    """
    all_data = await read_data_from_json()
    if all_data:
        for item in all_data:
            for user, data in item.items():
                if data[-1] == 'active':
                    start = BuyingTicketsNikulina(
                        event_filter=data[0],
                        all_user_data={
                            'user_id': int(user),
                            'data': {f"{user}": data}
                        },
                        bot=bot_
                    )
                    await start.run_parser()
    return


async def on_startup(dispatcher):
    if admin_id:
        await bot_.send_message(
            chat_id=admin_id,
            text='Бот запущен!'
        )

async def on_shutdown(dispatcher):
    if admin_id:
        await bot_.send_message(
            chat_id=admin_id,
            text='Бот остановлен 😥'
        )

async def start_bot() -> None:
    await bot_(DeleteWebhook(drop_pending_updates=True))

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await asyncio.gather(dp.start_polling(bot_), check_pars_event())
