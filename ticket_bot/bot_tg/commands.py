from .include import *

from aiogram.types import BotCommand, BotCommandScopeDefault


async def set_commands(bot: Bot = bot_):
    commands = [
        BotCommand(
            command="start",
            description="Запустить бота."
        ),
        BotCommand(
            command="help",
            description="Как использовать бота?"
        ),
        # BotCommand(
        #     command="func_2",
        #     description="func_2."
        # ),
        # BotCommand(
        #     command="func_2",
        #     description="func_2."
        # ),
        # BotCommand(
        #     command="func_3",
        #     description="func_3."
        # )
    ]

    await bot.set_my_commands(
        commands=commands,
        scope=BotCommandScopeDefault()
    )