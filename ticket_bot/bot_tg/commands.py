from .include import *

from aiogram.types import BotCommand, BotCommandScopeDefault


async def set_commands(bot: Bot = bot_):
    commands = [
        BotCommand(
            command="start",
            description="Запустить бота."
        ),
        BotCommand(
            command="add_filter",
            description="Установить мониторинг по фильтру."
        ),
    ]

    await bot.set_my_commands(
        commands=commands,
        scope=BotCommandScopeDefault()
    )