from .include import *

from .commands import set_commands


@dp.message(CommandStart())
async def start_cmd(message: Message):
    await set_commands()
    await message.answer(GREET_TEXT[0])
    await message.answer(GREET_TEXT[-1])
